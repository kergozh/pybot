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

    def __init__(self, config: Config):

        self._config   = config
        self._hostname = self._config.get("bot.hostname")   
        self._logger   = logging.getLogger(self._config.get("logger.name"))

        access_type = self._config.get("bot.access_type")  

        self._logger.info("init mastobot with access type " + access_type + " in " + self._hostname)

        match access_type:
            case 'AT': 
                self.access_token_access(self)

            case'CR':
                self.credential_access(self)

            case _:
                self._logger.error("access type not valid: " + access_type)
                sys.exit(0)


    @staticmethod
    def access_token_access(self):

        self._logger.debug("access token access in " + self._hostname)
    
        client_id     = self._config.get("access_token.client_id")
        secret        = self._config.get("access_token.secret")
        token         = self._config.get("access_token.token")
        self.mastodon = self.log_in(self, client_id, secret, token)    


    @staticmethod
    def credential_access(self):

        self._logger.debug("credential access in " + self._hostname)

        force_login       = self._config.get("credentials.force_login")
        secrets_file_path = self._config.get("credentials.secrets_directory") + "/" + self._config.get("credentials.secrets_file_path")

        self._logger.debug("force login      : " + str(force_login))
        self._logger.debug("secrets file path: " + secrets_file_path)

        is_setup = False

        if force_login:
            self.remove_file(self, secrets_file_path)     
        else:
            if self.check_file(self, secrets_file_path):
                is_setup = True

        if is_setup:
            client_id     = self.get_parameter(self,"client_id", secrets_file_path)
            secret        = self.get_parameter(self,"secret", secrets_file_path)
            token         = self.get_parameter(self,"token",  secrets_file_path)
            self.mastodon = self.log_in(self, client_id, secret, token)
        
        else:
            while(True):
                logged_in, self.mastodon = self.setup(secrets_file_path, self._hostname)

                if not logged_in:
                    self._logger.error("log in failed! Try again.")
                else:
                    break


    @staticmethod
    def remove_file(self, file_path):

        if os.path.exists(file_path):
            self._logger.debug("removing file: " + file_path)
            os.remove(file_path)


    @staticmethod
    def check_file(self, file_path):

        file_exits = False

        if not os.path.isfile(file_path):
            self._logger.debug("file " + file_path + " not found, running setup.")
            return
        else:
            self._logger.debug("file " + file_path + " found.")
            file_exits = True
            return file_exits


    @staticmethod
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


    @staticmethod
    def get_parameter(self, parameter, file_path):

        with open( file_path ) as f:
            for line in f:
                if line.startswith( parameter ):
                    return line.replace(parameter + ":", "").strip()

        self._logger.error(file_path + " missing parameter " + parameter)
        sys.exit(0)


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
                        self.modify_file(self, secrets_file_path, "client_id: ", value=line.rstrip())

                    elif cnt == 2:
                        self._logger.info("writing secret to " + secrets_file_path)
                        self.modify_file(self, secrets_file_path, "secret: ", value=line.rstrip())

                    line = fp.readline()
                    cnt += 1

            token_path = 'app_usercred.txt'

            with open(token_path) as fp:
                line = fp.readline()
                self._logger.info("writing token to " + secrets_file_path)
                self.modify_file(self, secrets_file_path, "token: ", value=line.rstrip())

            self.remove_file(self, "app_clientcred.txt")     
            self.remove_file(self, "app_usercred.txt")     

            self._logger.info("secrets setup done!")

        except Exception as e:
            self._logger.exception(e)
        
        return (logged_in, mastodon)


    @staticmethod
    def check_keyword_in_nofit(self, notif, keyword):

        text = notif.status.content

        self._logger.debug("Original keyword: " + keyword + " with " + str(len(keyword)))
        self._logger.debug("Original content: " + text)

        found   = False
        keyword = keyword.lower()
        
        content = self.cleanhtml(self, text)
        content = self.unescape(self, content)
        content = content.lower()
            
        self._logger.debug("Changed keyword: " + keyword + " with " + str(len(keyword)))
        self._logger.debug("Changed content: " + content)

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

            keyword_length = len(keyword)

            if unidecode.unidecode(content)[0:keyword_length] == keyword:
                found = True

        except:
            pass

        return (found)


    @staticmethod
    def cleanhtml(self, raw_html):

        cleanr = re.compile('<.*?>')
        cleantext = re.sub(cleanr, '', raw_html)
        return cleantext


    @staticmethod
    def unescape(self, s):

        s = s.replace("&apos;", "'")
        return s


    def replay(self, notif, aux_text):

        id         = notif.id
        username   = notif.account.acct
        status_id  = notif.status.id
        visibility = notif.status.visibility

        post_text  = f"@{username}{aux_text}"
        post_text = (post_text[:400] + '... ') if len(post_text) > 400 else post_text

        self._logger.debug("replaying notification " + str(id) + " with\n" + post_text)
        self.mastodon.status_post(post_text, in_reply_to_id=status_id,visibility=visibility)


    @staticmethod
    def modify_file(self, file_name, pattern,value=""):

        fh=fileinput.input(file_name,inplace=True)

        for line in fh:
            replacement=pattern + value
            line=re.sub(pattern,replacement,line)
            sys.stdout.write(line)

        fh.close()


