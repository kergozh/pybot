###
# Utilidad para gestionar la configuración de una aplicación python
# Fork del original de @arnaus@mastodont.cat
# En https://github.com/XaviArnaus/python-bundle
###  

from .storage import Storage

CONFIG_FILENAME = "config.yaml"

class Config (Storage):

    def __init__(self, filename: str = CONFIG_FILENAME) -> None:

        super().__init__(filename = filename)


    def get(self, param_name: str = "", default_value: any = None) -> any:

        if param_name.find(".") > 0:
            local_config = self._storage

            for item in param_name.split("."):
                if local_config[item]:
                    local_config = local_config[item]
                else:
                    return default_value

            return local_config

        return self._storage[param_name] if self._storage[param_name] else default_value
    