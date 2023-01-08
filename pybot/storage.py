###
# Clase esqueleto para la gestión de un fichero ymal 
# Fork del original de @arnaus@mastodont.cat
# En https://github.com/XaviArnaus/python-bundle
###  

import csv
import os
import os.path
import yaml

class Storage:
    def __init__(self, filename, directory) -> None:

        if directory == "" or directory == None:
            self._filepath = filename
        else:    
            if not os.path.exists(directory):
                os.makedirs(directory)
            self._filepath = directory + "/" + filename


    def read_yaml(self) -> None:
    
        with open(self._filepath, 'r', encoding='utf-8') as stream:
            self._storage = yaml.load(stream.read(), Loader=yaml.FullLoader)


    def read_csv(self) -> None:
    
        with open(self._filepath, newline = '') as fp:
            rows = csv.reader(fp)
            for row in rows:   
                self._storage.append(row)

    def write_row(self, row) -> None:
    
        with open(self._filepath, 'w', newline="") as fp:
            writer = csv.writer(fp)
            writer.writerow(row)


    def add_row(self, row) -> None:
    
        with open(self._filepath, 'a', newline="") as fp:
            writer = csv.writer(fp)
            writer.writerow(row)


