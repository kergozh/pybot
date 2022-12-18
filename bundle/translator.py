###
# Utilidad para la internalización de los literales de un programa python
###  

from .storage import Storage

DICTIONARY_FILENAME = "locale.yaml"
ERROR_MISSAGE       = " text id not found"
IN_ERROR_MISSAGE    = " in "
OR_ERROR_MISSAGE    = " or default language "

class Translator (Storage):

    def __init__(self, default_language: str, filename: str = DICTIONARY_FILENAME) -> None:

        self._default_language = default_language
        self._fixed_language   = default_language

        super().__init__(filename, "")
        self.read_yaml()

   
    def get_text(self, text_id: any, language = "") -> str:

        if language == "":
            language = self._fixed_language 

        if text_id in self._storage:
            local_dict = self._storage [text_id]

            if language in local_dict:
                local_dict = local_dict [language]

            else:
                if self._default_language in local_dict:
                    local_dict = local_dict[self._default_language]
                else: 
                    local_dict = str(text_id) + ERROR_MISSAGE + IN_ERROR_MISSAGE + language + OR_ERROR_MISSAGE + self._default_language
                    
        else:
            local_dict = str(text_id) + ERROR_MISSAGE

        return local_dict


    def fix_language(self, language) -> None:

        self._fixed_language = language

