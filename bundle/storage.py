###
# Clase esqueleto para la gestión de un fichero ymal 
# Fork del original de @arnaus@mastodont.cat
# En https://github.com/XaviArnaus/python-bundle
###  

import yaml

class Storage:
    def __init__(self, filename) -> None:

        self._filename = filename
        self._storage = {}
        self.read_file()


    def read_file(self) -> None:
    
        with open(self._filename, 'r') as stream:
            self._storage = yaml.safe_load(stream)


    def get(self, param_name: str = "", default_value: any = None) -> any:
    
        pass


    def get_all(self) -> dict:
    
        return self._storage


    def set(self, param_name: str, value: any = None):
    
        if param_name == None:
            raise RuntimeError("Params must have a name")
        self._storage[param_name] = value