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
        now_year   = now.strftime("%Y")
        now_month  = now.strftime("%m")
        now_day    = now.strftime("%d")
        now_hour   = now.strftime("%H")
        now_minute = now.strftime("%M")
 
        if "*" in hours:
            # True si no lo hemos hecho ya en este día-hora.
            if now_year != self._year or now_month != self._month or now_day != self._day or now_hour != self._hour:
                check = True
        else: 
            for hour2check in hours:
                if hour2check == now_hour:
                    # True si no lo hemos hecho ya en este día-hora 
                    if now_year != self._year or now_month != self._month or now_day != self._day or now_hour != self._hour:
                        check = True

                # Si se pide (restore), comprobamos hoy se ha pasado la hora y el programmer no se ha ejecutado.
                # Para ver si se saltaron las últimas horas de ayer habría que complicar el algoritmo :-)
                else:
                    if now_hour > hour2check and restore:
                        if (now_year == self._year and now_month == self._month and now_day == self._day and hour2check > self._hour) or \
                           (self._year == "" and self._month == "" and self._day == "" and self._hour == ""):                        
                            check = True

        if check:
            row = [now_year, now_month, now_day, now_hour, now_minute]
            self.write_row(row) 

        return check 
