# Simple class to hold all details relating to a mole in the database

class Mole:
    def __init__(self, unique_id, mole_id, date, pic, x, y):
        self.unique_id = unique_id
        self.id = mole_id
        self.date = date
        self.pic = pic
        self.x = x
        self.y = y

