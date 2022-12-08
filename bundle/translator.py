import yaml

DICTIONARY_FILENAME = "locale.yaml"
ERROR_MISSAGE       = " text id not found"
IN_ERROR_MISSAGE    = " in "
OR_ERROR_MISSAGE    = " or default language "


class Translator:
    def __init__(self, default_language: str) -> None:
        self._dicctionaty = {}
        self._default_language = default_language
        self._fixed_language   = default_language
        
        self.read_file()

    def read_file(self) -> None:
        with open(DICTIONARY_FILENAME, 'r') as stream:
            self._dicctionaty = yaml.safe_load(stream)
    
    def get_text(self, text_id: any, language = "") -> str:

        if language == "":
            language = self._fixed_language 

        if text_id in self._dicctionaty:
            local_dict = self._dicctionaty [text_id]

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

        return 

    def get_all(self) -> dict:
        return self._dicctionaty
