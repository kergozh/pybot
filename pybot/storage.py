"""
Clase esqueleto para la gestión de un fichero ymal o csv 
Inspirada en el original de @arnaus@mastodont.cat
En https://github.com/XaviArnaus/python-bundle
"""   

import csv
import os
import os.path
import yaml

class Storage:
    def __init__(self, filename, directory) -> None:
        """ constructor. si el directorio no existe lo crea """

        if directory == "" or directory == None:
            self._filepath = filename
        else:    
            if not os.path.exists(directory):
                os.makedirs(directory)
            self._filepath = directory + "/" + filename


    def read_yaml(self) -> None:
        """ este método carga el contenido del yaml en un dict. """
        """ se usa load en lugar de safeload para poder usar tags pasa cargar en tuples"""
    
        if os.path.exists(self._filepath):
            with open(self._filepath, 'r', encoding='utf-8') as stream:
                self._storage = yaml.load(stream.read(), Loader=yaml.FullLoader)
        else:
            self._storage = {}


    def read_csv(self) -> None:
        """ este método carga un fichero csv en una list """
    
        self._storage = []
        if os.path.exists(self._filepath):
            with open(self._filepath, newline = '') as fp:
                lines = csv.reader(fp)
                for line in lines:
                    for row in line:
                        self._storage.append(row)
        

    def write_row(self, row) -> None:
        """ este metodo escribe una lista como una línea de un fichero csv """
    
        with open(self._filepath, 'w', newline="") as fp:
            writer = csv.writer(fp)
            writer.writerow(row)


    def add_row(self, row) -> None:
        """ este metodo escribe una lista como una nueva línea añadida a un fichero csv """
    
        with open(self._filepath, 'a', newline="") as fp:
            writer = csv.writer(fp)
            writer.writerow(row)


