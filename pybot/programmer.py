"""
Clase para gestionar un programador (scheduler) de acciones por horas
(seria posible también hacerlo por minutos, haciendo doble pasada sobre las horas,
pero de momento no se necesita :-) )
"""  

from pybot.storage import Storage
import os
import datetime

FILENAME = "pgm.csv"
DIRECTORY = "pgm"

class Programmer (Storage):

    def __init__(self, filename: str = FILENAME, directory: str = DIRECTORY) -> None:
        """ init method

        Args:
            filename (str, optional): filename for control file. Defaults to FILENAME.
            directory (str, optional): directory for control file. Defaults to DIRECTORY.
        """

        self._year = ""
        self._month = ""
        self._day = ""
        self._hour = ""
        self._storage = []

        super().__init__(filename, directory)
        
        if os.path.exists(self._filepath):
            self.read_csv()
            if len(self._storage) == 5:
                self._year  = self._storage[0]
                self._month = self._storage[1]
                self._day   = self._storage[2]
                self._hour  = self._storage[3]
                              

    def check_time(self, hours, restore):
        """ check if it is time for performing an action

        Args:
            hours (list): list of hours when the action has to be done
            restore (bool): do the action if the time has passed

        Returns:
            bool: True if the action has to be done.
        """        

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
