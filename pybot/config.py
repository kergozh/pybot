###
# Utilidad para gestionar la configuración de una aplicación python
# Fork del original de @arnaus@mastodont.cat
# En https://github.com/XaviArnaus/python-bundle
###  

from .storage import Storage

CONFIG_FILENAME = "config.yaml"

class Config (Storage):

    def __init__(self, filename: str = CONFIG_FILENAME) -> None:

        super().__init__(filename, "")
        self.read_yaml()


    def get(self, param_name: str = "", default_value: any = None) -> any:

        error = False

        if param_name.find(".") > 0:
            
            local_config = self._storage

            for item in param_name.split("."):
                if item in local_config:
                    local_config = local_config[item]
                else:
                    error = True
                    output = default_value
            
            if not error: 
                output = local_config

        else:
            output = self._storage[param_name] if param_name in self._storage else default_value

        return output


    def exist (self, param_name: str = "") -> bool:

        found = False
        error = False

        if param_name.find(".") > 0:
            local_config = self._storage

            for item in param_name.split("."):
                if item in local_config:
                    local_config = local_config[item]
                else:
                    error = True

            if not error: 
                found = True

        else:
            found = True if param_name in self._storage else False

        return found

