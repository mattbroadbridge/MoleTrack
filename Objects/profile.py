import sys
import traceback
from os import path, mkdir, getlogin
from datetime import datetime
import sqlite3


# Handles all calls to the SQLite database
class Profile:
    def __init__(self, name, home_path):
        self.name = name
        self.home_path = home_path
        if not path.exists(self.home_path):
            mkdir(self.home_path)
        self.con = sqlite3.connect(path.join(home_path, "Database.db"))
        self.cur = self.con.cursor()

        sql_create_moles_table = """ CREATE TABLE IF NOT EXISTS moles (
                                                id integer PRIMARY KEY,
                                                moleID integer,
                                                xcoord integer,
                                                ycoord integer,
                                                datet datetime,
                                                picture blob
                                            ); """

        self.cur.execute(sql_create_moles_table)

    # Add a picture with the same moleID.
    def add_existing_record(self, moleID, xcoord, ycoord, pic):
        now = datetime.now()

        # get current time to add mole, if needed this can be
        # changed so the user inputs the time, but this is less hassle
        dt_string = now.strftime("%d/%m/%Y %H:%M:%S")

        sql = ''' INSERT INTO moles(moleID,xcoord,ycoord,picture,datet)
              VALUES(?,?,?,?,?) '''
        self.cur.execute(sql, (moleID, xcoord, ycoord, pic, dt_string))
        self.con.commit()

    # Add a new record of a mole, generating a new ID for that mole.
    def add_new_record(self, xcoord, ycoord, pic):
        now = datetime.now()

        # get current time to add mole, if needed this can be
        # changed so the user inputs the time, but this is less hassle
        dt_string = now.strftime("%d/%m/%Y %H:%M:%S")

        res = self.cur.execute("Select MAX(moleID + 0) from moles").fetchone()

        if res[0] is None:
            moleID = 1
        else:
            moleID = int(res[0]) + 1

        sql = ''' INSERT INTO moles(moleID,xcoord,ycoord,picture,datet)
              VALUES(?,?,?,?,?) '''
        self.cur.execute(sql, (moleID, xcoord, ycoord, pic, dt_string))
        self.con.commit()

    # This function is used to return the coords of each mole to draw points on the outline. Also used to determine
    # which mole is closest to the cursor.
    def return_mole_coords(self):
        return self.cur.execute('SELECT DISTINCT moleID, xcoord, ycoord from moles')

    # This returns all photos and dates for a single mole
    def get_mole_details(self, moleID):
        try:
            sql = 'SELECT id, moleID, datet, picture, xcoord, ycoord FROM moles WHERE moleID = ' + str(moleID)
            res = self.cur.execute(sql)
        except sqlite3.Error as er:
            print('SQLite error: %s' % (' '.join(er.args)))
            print("Exception class is: ", er.__class__)
            print('SQLite traceback: ')
            exc_type, exc_value, exc_tb = sys.exc_info()
            print(traceback.format_exception(exc_type, exc_value, exc_tb))
        return res

    def close_db(self):
        self.cur.close()
        self.con.close()

    # Convert digital data to binary format so it can be stored in database
    def convertToBinaryData(self, filename):
        with open(filename, 'rb') as file:
            blob_data = file.read()
        return blob_data

    # Remove a picture from a mole record
    def removeMolePic(self, uniqueID):
        sql = 'DELETE FROM moles WHERE id = ' + str(uniqueID)
        self.cur.execute(sql)
        self.con.commit()

    # Remove all pictures of a mole
    def removeMole(self, moleID):
        sql = 'DELETE FROM moles WHERE moleID = ' + str(moleID)
        self.cur.execute(sql)
        self.con.commit()
