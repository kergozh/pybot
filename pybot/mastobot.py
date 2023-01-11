###
# Mastobot, clase sobre mastodon.py orientada a hacer bots
# Fork del original de @spla@mastodont.cat
# En https://git.mastodont.cat/spla/info
###  

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

from .logger import Logger
from .translator import Translator
from .programmer import Programmer
from .config import Config
from .storage import Storage

MAX_LENGTH = 490

class Mastobot:

    def __init__(self, botname):

        self._config     = Config()
        self._logger     = Logger(self._config).getLogger()

        self._logger.info("init " + botname)

        self.init_app_options()
        self.init_bot_connection()
        
        self._me = "@" + self.mastodon.me()["username"].strip()
        self._logger.debug("me: " + self._me)


    def run(self, botname):

        self._logger.info("end " + botname)


    def init_app_options(self):

        self._hostname      = self._config.get("bot.hostname")   
        self._access_type   = self._config.get("bot.access_type")  

        self._actions       = Config(self._config.get("app.actions_file_name"))
        self._post_disabled = self._config.get("testing.disable_post")

        if "test_file"  in self._config.get("testing"):
            self._test_file = self._config.get("testing.test_file")
        else:
            self._test_file = False
                
        if self._test_file:
            self._post_disabled = True
        else:
            self._post_disabled = self._config.get("testing.disable_post")

        self._logger.debug("test file    : "    + str(self._test_file))
        self._logger.debug("post disabled: "    + str(self._post_disabled))


    def init_bot_connection(self):

        if self._access_type ==  'AT': 
                self.access_token_access()
         
        elif self._access_type ==  'CR': 
            self.credential_access()

        else:
            self._logger.error("access type not valid: " + self._access_type)
            raise RuntimeError


    def init_publish_bot(self):

        self._user_mention  = self._config.get("testing.user_mention")
        force_mention       = self._config.get("testing.force_mention")

        self._logger.debug("user_mention: "  + self._user_mention)
        self._logger.debug("force_mention: " + str(force_mention))

        if self._user_mention != "" and force_mention:
            self._force_mention = True
        else:
            self._force_mention = False 


    def init_replay_bot(self):

        if self._test_file:
            self._dismiss_disabled = True
        else:
            self._dismiss_disabled = self._config.get("testing.disable_dismiss")

        self._test_word        = self._config.get("testing.text_word").lower()
        ignore_test_toot       = self._config.get("testing.ignore_test_toot")

        self._logger.debug("dismiss disabled: " + str(self._dismiss_disabled))
        self._logger.debug("test_word: "        + self._test_word)
        self._logger.debug("ignore test: "      + str(ignore_test_toot))

        if self._test_word != "" and ignore_test_toot:
            self._ignore_test = True
        else:
            self._ignore_test = False 


    def init_translator(self, default_lenguage : str = "es"):

        self._translator = Translator(default_lenguage)


    def init_programmer(self):

        self._programmer = Programmer()
        self._force_programmer = self._config.get("testing.force_programmer")


    def init_output_file(self):

        directory = self._config.get("app.output_directory")
        filename  = self._config.get("app.output_file_name")
        self._output_file = Storage(filename, directory)
        self._disable_write = self._config.get("testing.disable_write")


    def init_input_data(self):

        self._data = Config(self._config.get("app.data_file_name"))


    def access_token_access(self):

        self._logger.debug("access token access in " + self._hostname)
    
        client_id     = self._config.get("access_token.client_id")
        secret        = self._config.get("access_token.secret")
        token         = self._config.get("access_token.token")
        self.mastodon = self.log_in(client_id, secret, token)    


    def credential_access(self):

        self._logger.debug("credential access in " + self._hostname)

        force_login       = self._config.get("credentials.force_login")
        secrets_file_path = self._config.get("credentials.secrets_directory") + "/" + self._config.get("credentials.secrets_file_name")

        self._logger.debug("force login      : " + str(force_login))
        self._logger.debug("secrets file path: " + secrets_file_path)

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
            self._logger.debug("file " + file_path + " not found, running setup.")
            return
        else:
            self._logger.debug("file " + file_path + " found.")
            file_exits = True
            return file_exits


    def log_in(self, client_id, secret, token):

        self._logger.debug("client id: " + client_id)
        self._logger.debug("secret   : " + secret)
        self._logger.debug("token    : " + token)

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

        self._logger.error(file_path + " missing parameter " + parameter)
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
                self._logger.info(secrets_file_path + " created!")

            with open(secrets_file_path, 'a') as the_file:
                self._logger.info("writing secrets parameter names to " + secrets_file_path)
                the_file.write('client_id: \n'+'secret: \n'+'token: \n')

            client_path = 'app_clientcred.txt'

            with open(client_path) as fp:

                line = fp.readline()
                cnt = 1

                while line:
                    if cnt == 1:
                        self._logger.info("writing client id to " + secrets_file_path)
                        self.modify_file(secrets_file_path, "client_id: ", value=line.rstrip())

                    elif cnt == 2:
                        self._logger.info("writing secret to " + secrets_file_path)
                        self.modify_file(secrets_file_path, "secret: ", value=line.rstrip())

                    line = fp.readline()
                    cnt += 1

            token_path = 'app_usercred.txt'

            with open(token_path) as fp:
                line = fp.readline()
                self._logger.info("writing token to " + secrets_file_path)
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
                text = (text[:MAX_LENGTH] + '... ') if len(text) > MAX_LENGTH else text

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

        self._logger.debug("process notif type: " + notif_type)

        dismiss = True
        content = ""

        if notif.type == notif_type:

            content = self.clean_content(notif.status.content)

            # sólo si la notificacions va dirigida al bot
            if content.find(self._me) != 0:
                content = ""

            else:
                if self._ignore_test and content.find(self._test_word) != -1:
                    self._logger.debug("ignoring test notification id " + str(notif.id))
                    dismiss = False
                    content = ""            

                else:
                    content = self.clean_content(notif.status.content)
                    content = content.replace(self._me, "")
                    content = content.replace(self._test_word, "")
                    content = content.strip()
                    
                    if self._dismiss_disabled:
                        self._logger.debug("notification replayed but dismiss disabled in id " + str(notif.id))               
                        dismiss = False    

        if dismiss:
            self._logger.debug("dismissing notification id " + str(notif.id))              
            self.mastodon.notifications_dismiss(notif.id)

        self._logger.debug("content: " + content)

        return content


    def clean_content(self, text):

        self._logger.debug("Original content: " + text)
        
        text = self.cleanhtml(text)
        text = self.unescape(text)
        text = text.lower()
            
        self._logger.debug("Checking content: " + text)

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
            self._logger.info("checking programmer with " + str(hours) + " resultat " + str(check))                    

        return check


    def write_output_file (self, row):

        if self._disable_write:
            self._logger.debug("write output file disabled")                    
            check = True
        else:
            self._output_file.add_row(row)
            self._logger.info("output file written")                    
