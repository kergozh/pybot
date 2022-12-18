###
# Clase para gestionar un programador de acciones por horas
# (seria posible también hacerlo por minutos, haciendo doble pasada sobre las horas,
# pero de momento no se necesita :-) )
###  

from .storage import Storage
import os
import datetime
import csv

FILENAME = "pgm.csv"
DIRECTORY = "pgm"

class Programmer (Storage):

    def __init__(self, filename: str = FILENAME, directory: str = DIRECTORY) -> None:

        self._year = ""
        self._month = ""
        self._day = ""
        self._hour = ""
        self._storage = []

        super().__init__(filename, directory)
        
        if os.path.exists(self._filepath):
            self.read_csv()
            rows = self._storage
            for row in rows:
                if len(row) == 5:
                    self._year  = row[0]
                    self._month = row[1]
                    self._day   = row[2]
                    self._hour  = row[3]
                              

    def check_time(self, hours, restore):
        
        check = False
        now = datetime.datetime.now()
        year = str(now.year)
        month = str(now.month)
        day = str(now.day)
        hour = str(now.hour)
        minute = str(now.minute)
 
        if "*" in hours:
            # True si no lo hemos hecho ya en este día-hora.
            if day != self._day or hour != self._hour:
                check = True
        else: 
            for hour2check in hours:
                # True si no lo hemos hecho ya en este día-hora 
                if hour == hour2check:
                    if day != self._day or hour != self._hour:
                        check = True

                # Si se pide (restore), comprobamos si se ha pasado la hora.
                else:
                    if hour > hour2check and restore:
                        if (year < self._year) or \
                           (year == self._year and month < self._month) or \
                           (year == self._year and month == self._month and day < self._day) or \
                           (year == self._year and month == self._month and day == self._day and hour2check > self._hour):
                           check = True

        if check:
            row = [year, month, day, hour, minute]
            self.write_row(row) 

        return check 
