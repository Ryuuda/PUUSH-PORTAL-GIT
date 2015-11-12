__author__ = 'Todd'

import peewee
import iodev.models
from iodev.models import *

db = SqliteDatabase('pushDEVDB.db')

def create_all_tables():
    db.create_tables([ User, Doarama, Activity, RaceCourse, DataLog, DataLogDoarama, Lap, SmartGaugeUser ])
    db.create_tables([ SmartGaugeUser ])


def create_SmartGaugeUser_table():
    db.create_table(SmartGaugeUser)
