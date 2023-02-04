""" 
Mastobot, clase sobre mastodon.py para hacer bots
Inspirada (pero cada vez más lejos) en el info bot de @spla@mastodont.cat
En https://git.mastodont.cat/spla/info
"""  

import logging
import getpass
import fileinput
import re
import os
import sys
import os.path
from types import SimpleNamespace

import unidecode
import yaml
from mastodon import Mastodon
from mastodon.Mastodon import MastodonMalformedEventError, MastodonNetworkError, MastodonReadTimeout, MastodonAPIError, MastodonIllegalArgumentError

from pybot.logger import Logger
from pybot.translator import Translator
from pybot.programmer import Programmer
from pybot.config import Config
from pybot.storage import Storage


class Mastobot:

    def __init__(self, botname):

        self._config = Config()
        self._logger = Logger(self._config).getLogger()

        self._logger.info("init %s", botname)

        self.init_app_options()
        self.init_bot_connection()
        
        self._me = "@" + self.mastodon.me()["username"].strip()
        self._logger.debug("me: %s", self._me)


    def run(self, botname):

        self._logger.info("end %s", botname)


    def init_app_options(self):

        self._hostname    = self._config.get("bot.hostname")   
        self._access_type = self._config.get("bot.access_type")  
        
        if self._config.exist("app.max_lenght"):
            self._max_lenght  = self._config.get("app.max_lenght")  
        else:
            self._max_lenght  = 490

        if self._config.exist("app.actions_file_name"):
            if self._config.get("app.actions_file_name") != "":
                self._logger.debug("action file found")
                self._actions = Config(self._config.get("app.actions_file_name"))

        if self._config.exist("app.data_file_name"):
            if self._config.get("app.data_file_name") != "":
                self._logger.debug("data file found")
                self._data = Config(self._config.get("app.data_file_name"))

        if self._config.exist("testing.test_file"):
            self._test_file = self._config.get("testing.test_file"):
            self._logger.debug("test file file found")
        else:
            self._test_file = False

        if self._test_file:
            if self._config.exist("testing.disable_post"):
                self._post_disabled = self._config.get("testing.disable_post")
            else:
                self._post_disabled = False

        self._logger.debug("max lenght: %s", str(self._max_lenght))
        self._logger.debug("post disabled: %s", str(self._post_disabled))


    def init_bot_connection(self):

        if self._access_type ==  'AT': 
                self.access_token_access()
         
        elif self._access_type ==  'CR': 
            self.credential_access()

        else:
            self._logger.error("access type not valid: %s", self._access_type)
            raise RuntimeError


    def init_publish_bot(self):

        if self._config.exist("testing.force_mention"):
            self._force_mention = self._config.get("testing.force_mention")
            if self._force_mention: 
                self._user_mention  = self._config.get("testing.user_mention")
        else:
            self._force_mention = False

        self._logger.debug("force_mention: %s", str(self._force_mention))        


    def init_repetition_control(self):

        if self._config.exist("app.working_directory"): 
            directory = self._config.get("app.working_directory")
        else:
            directory = ""

        if self._config.exist("app.control_file_name"): 
            filename = self._config.get("app.control_file_name")
        else:
            filename  = "ctr.csv"

        self._control_file = Storage(filename, directory)
        self._control_file.read_csv()


    def init_replay_bot(self):

        if self._test_file:
            # Con test file no permitimos dismiss (daria error)
            self._dismiss_disabled = True
        else:
            if self._config.exist("testing.disable_dismiss"):
                self._dismiss_disabled = self._config.get("testing.disable_dismiss")
            else:
                self._dismiss_disabled = False

        if self._config.exist("testing.ignore_test_toot"):
            self._ignore_test = self._config.get("testing.ignore_test_toot")
            if self._ignore_test:  
                self._test_word = self._config.get("testing.text_word").lower()
        else:
            self._ignore_test = False

        self._logger.debug("dismiss disabled: %s", str(self._dismiss_disabled))
        self._logger.debug("ignore test: %s", str(self._ignore_test))


    def init_translator(self, default_lenguage : str = "es"):

        self._translator = Translator(default_lenguage)


    def init_programmer(self):

        if self._config.exist("app.working_directory"): 
            directory = self._config.get("app.working_directory")
        else:
            directory = ""

        if self._config.exist("app.programmer_file_name"): 
            filename = self._config.get("app.programmer_file_name")
        else:
            filename  = "pgm.csv"

        self._programmer = Programmer(filename, directory)
        self._force_programmer = self._config.get("testing.force_programmer")


    def init_output_file(self):

        if self._config.exist("app.working_directory"): 
            directory = self._config.get("app.working_directory")
        else:
            directory = ""

        if self._config.exist("app.output_file_name"): 
            filename = self._config.get("app.output_file_name")
        else:
            filename  = "output.csv"

        self._output_file = Storage(filename, directory)
        
        if self._config.exist("testing.disable_write"):
            self._disable_write = self._config.get("testing.disable_write")
        else:
            self._disable_write = False


    def access_token_access(self):

        self._logger.debug("access token access in %s", self._hostname)
    
        client_id     = self._config.get("access_token.client_id")
        secret        = self._config.get("access_token.secret")
        token         = self._config.get("access_token.token")
        self.mastodon = self.log_in(client_id, secret, token)    


    def credential_access(self):

        self._logger.debug("credential access in %s", self._hostname)

        force_login       = self._config.get("credentials.force_login")
        secrets_file_path = self._config.get("credentials.secrets_directory") + "/" + self._config.get("credentials.secrets_file_name")

        self._logger.debug("force login: %s", str(force_login))
        self._logger.debug("secrets file path: %s", secrets_file_path)

        is_setup = False

        if force_login:
            self.remove_file(secrets_file_path)     
        else:
            if self.check_file(secrets_file_path):
                is_setup = True

        if is_setup:
            client_id     = self.get_parameter("client_id", secrets_file_path)
            secret        = self.get_parameter("secret", secrets_file_path)
            token         = self.get_parameter("token",  secrets_file_path)
            self.mastodon = self.log_in(client_id, secret, token)
        
        else:
            while(True):
                logged_in, self.mastodon = self.setup(secrets_file_path)

                if not logged_in:
                    self._logger.error("log in failed! Try again.")
                else:
                    break


    @staticmethod
    def remove_file(file_path):

        if os.path.exists(file_path):
            os.remove(file_path)


    def check_file(self, file_path):

        file_exits = False

        if not os.path.isfile(file_path):
            self._logger.debug("file %s not found, running setup", file_path)
            return
        else:
            self._logger.debug("file %s found", file_path)
            file_exits = True
            return file_exits


    def log_in(self, client_id, secret, token):

        self._logger.debug("client id: %s", client_id)
        self._logger.debug("secret: %s", secret)
        self._logger.debug("token: %s", token)

        self.mastodon = Mastodon(
            client_id = client_id,
            client_secret = secret,
            access_token = token,
            api_base_url = 'https://' + self._hostname,
        )

        return (self.mastodon)


    def get_parameter(self, parameter, file_path):

        with open( file_path ) as f:
            for line in f:
                if line.startswith( parameter ):
                    return line.replace(parameter + ":", "").strip()

        self._logger.error("%s missing parameter %s", file_path, parameter)
        raise RuntimeError 


    def setup(self, secrets_file_path):

        self._logger.debug("mastobot setup")

        logged_in = False

        try:
            user_name = input("Enter Mastodon login e-mail (or 'q' to exit): ")

            if user_name == 'q':
                sys.exit("Bye")

            user_password = getpass.getpass("User password? ")
            
            app_name = self._config.get("bot.app_name")

            Mastodon.create_app(app_name, scopes=["read","write"],
                to_file="app_clientcred.txt", api_base_url=self._hostname)

            mastodon = Mastodon(client_id = "app_clientcred.txt", api_base_url = self._hostname)

            mastodon.log_in(
                user_name,
                user_password,
                scopes = ["read", "write"],
                to_file = "app_usercred.txt"
            )

            if os.path.isfile("app_usercred.txt"):
                self._logger.info("log in succesful!")
                logged_in = True

            secrets_directory = self._config.get("credentials.secrets_directory")
            if not os.path.exists(secrets_directory):
                os.makedirs(secrets_directory)

            if not os.path.exists(secrets_file_path):
                with open(secrets_file_path, 'w'): pass
                self._logger.info("%s created!", secrets_file_path)

            with open(secrets_file_path, 'a') as the_file:
                self._logger.info("writing secrets parameter names to %s", secrets_file_path)
                the_file.write('client_id: \n'+'secret: \n'+'token: \n')

            client_path = 'app_clientcred.txt'

            with open(client_path) as fp:

                line = fp.readline()
                cnt = 1

                while line:
                    if cnt == 1:
                        self._logger.info("writing client id to %s", secrets_file_path)
                        self.modify_file(secrets_file_path, "client_id: ", value=line.rstrip())

                    elif cnt == 2:
                        self._logger.info("writing secret to %s", secrets_file_path)
                        self.modify_file(secrets_file_path, "secret: ", value=line.rstrip())

                    line = fp.readline()
                    cnt += 1

            token_path = 'app_usercred.txt'

            with open(token_path) as fp:
                line = fp.readline()
                self._logger.info("writing token to %s", secrets_file_path)
                self.modify_file(secrets_file_path, "token: ", value=line.rstrip())

            self.remove_file("app_clientcred.txt")     
            self.remove_file("app_usercred.txt")     

            self._logger.info("secrets setup done!")

        except Exception as e:
            self._logger.exception(e)
        
        return (logged_in, mastodon)


    @staticmethod
    def modify_file(file_name, pattern, value = ""):

        fh=fileinput.input(file_name,inplace=True)

        for line in fh:
            replacement=pattern + value
            line=re.sub(pattern,replacement,line)
            sys.stdout.write(line)

        fh.close()


    def check_repetition(self, item: str, repetitions): 
        """ este método valida si el item esta en la lista, y controla que no crezca más allá de repetitions """
        """ ojo, item debe ser string """
        
        self._logger.debug("item: %s", item)  
        self._logger.debug("repetitions: %s", str(repetitions))  

        item_list = self._control_file._storage
        self._logger.debug("item list: %s", str(item_list))  

        valid = False if item in item_list else True
        self._logger.debug("valid: %s", str(valid))  

        if valid:
            item_list.append(item)
            if len(item_list) > repetitions:
                for i in range(len(item_list) - repetitions):
                    item_list.pop(0)

            self._logger.debug("item list: %s", str(item_list))          
            self._control_file.write_row(item_list)

        return valid


    def post_toot(self, text, language): 

        list      = []
        status_id = None

        if self._post_disabled:
            self._logger.info("posting answer disabled")                    

        else:
            if isinstance(text, str):
                list.append(text)
            else:
                list = text

            if self._force_mention:
                visibility = "direct"
                add_text = "@" + self._user_mention + "\n\n"
            else:
                visibility = "public" 
                add_text = ""

            for text in list:
 
                if add_text != "":
                    text = add_text + text
                text = (text[:self._max_lenght] + '... ') if len(text) > self._max_lenght else text

                self._logger.info("posting toot")
                status = self.mastodon.status_post(text, in_reply_to_id=status_id, visibility=visibility, language=language)
                status_id = status["id"] 


    def get_notifications(self):

        notifications = []
        
        if self._test_file:        
            with open(self._config.get("testing.test_file_name"), encoding='utf-8') as f:
                for linea in f:
                    mydict = {}
                    notif   = yaml.safe_load(linea)
                    account = SimpleNamespace(acct = notif["acct"])
                    status  = SimpleNamespace(id = notif["id2"], in_reply_to_id = notif["in_reply_to_id"], visibility = notif["visibility"], language = notif["language"], content = notif["content"])
                    mydict["id"] = notif["id"]
                    mydict["type"] = notif["type"]
                    mydict["account"] = account
                    mydict["status"] = status
                    mynam  = SimpleNamespace(**mydict)
                    notifications.append(mynam)

        else:
            notifications = self.mastodon.notifications()          

        return notifications


    def check_notif(self, notif, notif_type):

        self._logger.debug("process notif type: %s", notif_type)

        dismiss = True
        content = ""

        if notif.type == notif_type:

            content = self.clean_content(notif.status.content)

            # sólo si la notificacions va dirigida al bot
            if content.find(self._me) != 0:
                content = ""

            else:
                if self._ignore_test and content.find(self._test_word) != -1:
                    self._logger.debug("ignoring test notification id %s", str(notif.id))
                    dismiss = False
                    content = ""            

                else:
                    content = self.clean_content(notif.status.content)
                    content = content.replace(self._me, "")
                    content = content.replace(self._test_word, "")
                    content = content.strip()
                    
                    if self._dismiss_disabled:
                        self._logger.debug("notification replayed but dismiss disabled for id %s", str(notif.id))               
                        dismiss = False    

        if dismiss:
            self._logger.debug("dismissing notification id %s", str(notif.id))              
            self.mastodon.notifications_dismiss(notif.id)

        self._logger.debug("content: %s", content)

        return content


    def clean_content(self, text):

        self._logger.debug("Original content: %s", text)
        
        text = self.cleanhtml(text)
        text = self.unescape(text)
        text = text.lower()
            
        self._logger.debug("Checking content: %s", text)

        return text 


    def find_notif_word_list(self, text):

        text = self.clean_content(text)
            
        return text.split()


    @staticmethod
    def cleanhtml(raw_html):

        cleanr = re.compile('<.*?>')
        cleantext = re.sub(cleanr, '', raw_html)
        return cleantext


    @staticmethod
    def unescape(s):

        s = s.replace("&apos;", "'")
        return s


    def replay_toot(self, text, notif): 

        list       = []
        status_id  = notif.status.id
        visibility = notif.status.visibility
        language   = notif.status.language

        if self._post_disabled:
            self._logger.info("posting answer disabled")                    

        else:
            if isinstance(text, str):
                list.append(text)
            else:
                list = text
            
            for text in list:
                self._logger.debug("posting answer ")                    
                status = self.mastodon.status_post(text, in_reply_to_id=status_id, visibility=visibility, language=language)
                status_id = status["id"] 


    def check_programmer (self, hours, restore):

        if self._force_programmer:
            self._logger.debug("forced programmer")                    
            check = True
        else:
            check = self._programmer.check_time(hours, restore)
            self._logger.info("checking programmer with %s resultat: %s", str(hours), str(check))                    

        return check


    def add_output_file (self, row):

        if self._disable_write:
            self._logger.debug("write output file disabled")                    
            check = True
        else:
            self._output_file.add_row(row)
            self._logger.info("output file written")                    


    def write_output_file (self, row):

        if self._disable_write:
            self._logger.debug("write output file disabled")                    
            check = True
        else:
            self._output_file.write_row(row)
            self._logger.info("output file written")                    
