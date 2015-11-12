__author__ = 'Todd'

from peewee import *
import os
import datetime

path = os.path.dirname(os.path.abspath(__file__))
if 'fuel' in path:
    db = SqliteDatabase('pushFUELDB.db')
else:
    db = SqliteDatabase('pushDEVDB.db')


class User(Model):
    username = TextField(default='')
    realname = TextField(default='')
    email = TextField(unique=True)
    phone = TextField(default='')
    created = DateTimeField(default=datetime.datetime.utcnow)
    updated = DateTimeField(default=datetime.datetime.utcnow)
    fb_id = TextField(default='')            # Facebook id
    fb_profile_url = TextField(default='')   # Facebook profile url
    fb_access_token = TextField(default='')  # Facebook access token

    class Meta:
        database = db


class Doarama(Model):
    visual_key = TextField()
    bitly_hash = CharField(max_length=255, default='')

    class Meta:
        database = db


class Activity(Model):
    name = TextField()
    active = BooleanField(default=False)
    clamp_altitude_ground = BooleanField(default=False)
    doarama_activity_id = IntegerField(null=True)

    class Meta:
        database = db


class RaceCourse(Model):
    name = TextField()
    finline_out_lat = DoubleField()
    finline_out_lon = DoubleField()
    finline_in_lat = DoubleField()
    finline_in_lon = DoubleField()
    farthest_point = IntegerField()  # Furthest point on track from finish line in Meters

    class Meta:
        database = db


class DataLog(Model): # TODO: Change DataLog to Session
    user = ForeignKeyField(User, related_name='DataLogs')
    filepath = TextField(default='')
    performed = DateTimeField(default=datetime.datetime.utcnow)
    created = DateTimeField(default=datetime.datetime.utcnow)
    activity = ForeignKeyField(Activity, related_name='DataLogs')
    racecourse = ForeignKeyField(RaceCourse, related_name='DataLogs', null=True)

    class Meta:
        database = db


class DataLogDoarama(Model):
    datalog = ForeignKeyField(DataLog, related_name='Doaramas')
    doarama = ForeignKeyField(Doarama, related_name='DataLogs')

    class Meta:
        database = db


class Lap(Model):
    datalog = ForeignKeyField(DataLog, related_name='Laps')
    lap_num = IntegerField()
    lap_time = DoubleField()
    max_speed_mph = DoubleField()
    is_fastest_time = BooleanField(default=False)

    class Meta:
        database = db


class Point(Model):
    lap = ForeignKeyField(Lap, related_name='Points')
    type = TextField(default='')
    time = DateTimeField()
    speed_m_s = DoubleField()
    latitude = DoubleField()
    longitude = DoubleField()

    class Meta:
        database = db


class Split(Model):
    lap = ForeignKeyField(Lap, related_name='Splits')
    name = TextField(default='')
    split_time = DoubleField()

    class Meta:
        database = db

'''
class SmartGauge(Model):
    gauge_id = CharField(max_length=64)
    model_number = IntegerField()
    manufacture_date = DateTimeField()

    class Meta:
        database = db
'''


class SmartGaugeUser(Model):
    user = ForeignKeyField(User, related_name='SmartGauges')
    # smartgauge = ForeignKeyField(SmartGauge, related_name='Users')
    gauge_id = CharField(max_length=64)
    begin_date = DateTimeField(default=datetime.datetime.utcnow)
    end_date = DateTimeField(null=True)


    class Meta:
        database = db
