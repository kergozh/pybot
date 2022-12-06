###
# Mastobot, clase sobre mastodon.py orientada a hacer bots
# Fork del original de @spla@mastodont.cat
# En https://git.mastodont.cat/spla/info
###  

from .config import Config
from .logger import Logger
import logging
from mastodon import Mastodon
from mastodon.Mastodon import MastodonMalformedEventError, MastodonNetworkError, MastodonReadTimeout, MastodonAPIError, MastodonIllegalArgumentError
import getpass
import unidecode
import fileinput,re
import os
import sys
import os.path

###
# Dict helper class.
# Defined at top level so it can be pickled.
###
class AttribAccessDict(dict):

    def __getattr__(self, attr):

        if attr in self:
            return self[attr]
        else:
            raise AttributeError("Attribute not found: " + str(attr))

    def __setattr__(self, attr, val):

        if attr in self:
            raise AttributeError("Attribute-style access is read only")
        super(AttribAccessDict, self).__setattr__(attr, val)


class Mastobot:

    # name = 'Mastobot'
    # def __init__(self, mastodon=None, mastodon_hostname=None):

    def __init__(self, config: Config):

        self._config = config
        self._logger = logging.getLogger(self._config.get("logger.name"))

        force_login       = self._config.get("bot.force_login")
        secrets_file_path = self._config.get("bot.secrets_directory") + "/" + self._config.get("bot.secrets_file_path")
        config_file_path  = self._config.get("bot.config_directory") + "/" + self._config.get("bot.config_file_path")

        self._logger.info("init mastobot with force log in a " + str(force_login))
        self._logger.debug("secrets file path: " + secrets_file_path)
        self._logger.debug("config file path : " + config_file_path)

        if force_login:
            self.remove_file(self, secrets_file_path)     
            self.remove_file(self, config_file_path)     
            is_setup = False
        else:
            if self.check_file(self, secrets_file_path):
                if self.check_file(self, config_file_path):
                    is_setup = True
                else:
                    self.remove_file(self, secrets_file_path)
                    is_setup = False
            else:
                is_setup = False        

        if is_setup:
            self.mastodon, self.mastodon_hostname = self.log_in(self, secrets_file_path, config_file_path)
        else:
            while(True):
                logged_in, self.mastodon, self.mastodon_hostname = self.setup(secrets_file_path, config_file_path)

                if not logged_in:
                    self._logger.error("log in failed! Try again.")
                else:
                    break


    @staticmethod
    def remove_file(self, file_path):

        if os.path.exists(file_path):
            self._logger.info("removing file: " + file_path)
            os.remove(file_path)


    @staticmethod
    def check_file(self, file_path):

        file_exits = False

        if not os.path.isfile(file_path):
            self._logger.info("file " + file_path + " not found, running setup.")
            return
        else:
            self._logger.info("file " + file_path + " found.")
            file_exits = True
            return file_exits


    @staticmethod
    def log_in(self, secrets_file_path, config_file_path):

        self._logger.info("init log in.")

        uc_client_id     = self.get_parameter(self,"uc_client_id",     secrets_file_path)
        uc_client_secret = self.get_parameter(self,"uc_client_secret", secrets_file_path)
        uc_access_token  = self.get_parameter(self,"uc_access_token",  secrets_file_path)

        self.mastodon_hostname = self.get_parameter(self,"mastodon_hostname", config_file_path)

        self.mastodon = Mastodon(
            client_id = uc_client_id,
            client_secret = uc_client_secret,
            access_token = uc_access_token,
            api_base_url = 'https://' + self.mastodon_hostname,
        )

        headers={ 'Authorization': 'Bearer %s'%uc_access_token }

        return (self.mastodon, self.mastodon_hostname)


    @staticmethod
    def get_parameter(self, parameter, file_path ):

        with open( file_path ) as f:
            for line in f:
                if line.startswith( parameter ):
                    return line.replace(parameter + ":", "").strip()

        self._logger.error(file_path + " missing parameter " + parameter)
        sys.exit(0)


    def get_mention(self, notif, keyword):

        id         = notif.id
        account_id = notif.account.id
        username   = notif.account.acct
        status_id  = notif.status.id
        text       = notif.status.content
        visibility = notif.status.visibility

        reply, question = self.check_keyword(self, text, keyword)

        mention_dict = {'reply': reply, 'question': question, 'id': id, 'account_id': account_id, 'username': username, 'status_id': status_id, 'text': text, 'visibility': visibility}

        mention = self.__json_allow_dict_attrs(mention_dict)

        return mention


    @staticmethod
    def __json_allow_dict_attrs(json_object):
        """
        Makes it possible to use attribute notation to access a dicts
        elements, while still allowing the dict to act as a dict.
        """
        if isinstance(json_object, dict):
            return AttribAccessDict(json_object)
        return json_object


    @staticmethod
    def check_keyword(self, text, keyword):

        reply = False

        keyword = keyword.lower()
        
        self._logger.debug("checking " + keyword + " with " + str(len(keyword)))

        content = self.cleanhtml(self, text)
        content = self.unescape(self, content)
        content = content.lower()
            
        self._logger.debug("changed content: " + content)

        try:
            start = content.index("@")
            end = content.index(" ")
            if len(content) > end:
                content = content[0: start:] + content[end +1::]

            cleanit = content.count('@')

            i = 0
            while i < cleanit :
                start = content.rfind("@")
                end = len(content)
                content = content[0: start:] + content[end +1::]
                i += 1

            question = content

            keyword_length = len(keyword)

            if unidecode.unidecode(question)[0:keyword_length] == keyword:
                reply = True

        except:
            pass

        return (reply, question)


    @staticmethod
    def cleanhtml(self, raw_html):

        cleanr = re.compile('<.*?>')
        cleantext = re.sub(cleanr, '', raw_html)
        return cleantext


    @staticmethod
    def unescape(self, s):

        s = s.replace("&apos;", "'")
        return s


    def replay(self, mention, aux_text):

        post_text  = f"@{mention.username}{aux_text}"

        post_text = (post_text[:400] + '... ') if len(post_text) > 400 else post_text

        self._logger.debug("replaying notification " + mention.id + " with\n" + post_text)
        self.mastodon.status_post(post_text, in_reply_to_id=mention.status_id,visibility=mention.visibility)

    @staticmethod
    def modify_file(self, file_name, pattern,value=""):

        fh=fileinput.input(file_name,inplace=True)

        for line in fh:

            replacement=pattern + value
            line=re.sub(pattern,replacement,line)
            sys.stdout.write(line)

        fh.close()


    def setup(self, secrets_file_path, config_file_path):

        self._logger.info("init setup")

        logged_in = False

        try:

            self.mastodon_hostname = input("Enter Mastodon hostname (or 'q' to exit): ")

            if self.mastodon_hostname == 'q':

                sys.exit("Bye")

            user_name = input("User email, ex. user@" + self.mastodon_hostname +"? ")
            user_password = getpass.getpass("User password? ")
            
            app_name = self._config.get("bot.app_name")

            Mastodon.create_app(app_name, scopes=["read","write"],

                    to_file="app_clientcred.txt", api_base_url=self.mastodon_hostname)

            mastodon = Mastodon(client_id = "app_clientcred.txt", api_base_url = self.mastodon_hostname)

            mastodon.log_in(
                user_name,
                user_password,
                scopes = ["read", "write"],
                to_file = "app_usercred.txt"
            )

            if os.path.isfile("app_usercred.txt"):

                self._logger.info("log in succesful!")
                logged_in = True

            secrets_directory = self._config.get("bot.secrets_directory")
            if not os.path.exists(secrets_directory):
                os.makedirs(secrets_directory)

            if not os.path.exists(secrets_file_path):
                with open(secrets_file_path, 'w'): pass
                self._logger.info(secrets_file_path + " created!")

            with open(secrets_file_path, 'a') as the_file:
                self._logger.info("writing secrets parameter names to " + secrets_file_path)
                the_file.write('uc_client_id: \n'+'uc_client_secret: \n'+'uc_access_token: \n')

            client_path = 'app_clientcred.txt'

            with open(client_path) as fp:

                line = fp.readline()
                cnt = 1

                while line:

                    if cnt == 1:

                        self._logger.info("writing client id to " + secrets_file_path)
                        self.modify_file(self, secrets_file_path, "uc_client_id: ", value=line.rstrip())

                    elif cnt == 2:

                        self._logger.info("writing client secret to " + secrets_file_path)
                        self.modify_file(self, secrets_file_path, "uc_client_secret: ", value=line.rstrip())

                    line = fp.readline()
                    cnt += 1

            token_path = 'app_usercred.txt'

            with open(token_path) as fp:

                line = fp.readline()
                self._logger.info("writing access token to " + secrets_file_path)
                self.modify_file(self, secrets_file_path, "uc_access_token: ", value=line.rstrip())

            self.remove_file(self, "app_clientcred.txt")     
            self.remove_file(self, "app_usercred.txt")     

            config_directory = self._config.get("bot.config_directory")
            if not os.path.exists(config_directory):
                os.makedirs(config_directory)

            if not os.path.exists(config_file_path):
                with open(config_file_path, 'w'): pass
                self._logger.info(config_file_path + " created!")
      
            with open(config_file_path, 'a') as the_file:
                the_file.write('mastodon_hostname: \n')
                self._logger.info("adding parameter 'mastodon_hostname' to " + config_file_path)
   
            self.modify_file(self, config_file_path, "mastodon_hostname: ", value=self.mastodon_hostname)
    
            self._logger.info("secrets setup done!")

        except Exception as e:
            self._logger.exception(e)
        
        return (logged_in, mastodon, self.mastodon_hostname)