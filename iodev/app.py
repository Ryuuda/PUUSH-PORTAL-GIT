#  Upload Template From: https://github.com/kirsle/flask-multi-upload

import os
import re
import json
import glob
from uuid import uuid4
from flask import Flask, g, request, redirect, url_for, render_template
import peewee
import urllib
from datetime import datetime

path = os.path.dirname(os.path.abspath(__file__))
if 'fuel' in path:
    from fuel.models import *
else:
    from iodev.models import *

LOCAL_DEVELOPMENT = False

ALLOWED_EXTENSIONS = ['txt', 'csv', 'dat']

app = Flask(__name__)

if 'fuel' in path:
    # Production
    PUSH_APP_URL = "http://fuel.pushthelimit.net"
    FACEBOOK_APP_ID = '883442311724568'
    DOARAMA_BASEURL = "https://api.doarama.com"
    GOOGLE_ANALYTICS_ID = 'UA-55514623-3'
    BASE_DIR = "fuel"
else:
    # Development
    PUSH_APP_URL = 'http://dev.pushthelimit.io'
    FACEBOOK_APP_ID = '883450915057041'
    DOARAMA_BASEURL = "https://doarama-thirdparty-dev.herokuapp.com"
    GOOGLE_ANALYTICS_ID = 'UA-55514623-2'
    BASE_DIR = "iodev"

@app.route("/")
def index():

    return render_template("index.html")


@app.route("/register_user", methods=['GET'])
def register_user_get():

    return render_template("register_user.html")


@app.route('/register_user', methods=['POST'])
def register_user_post():
    form = request.form
    # Is the upload using Ajax, or a direct POST by the form?
    is_ajax = False
    if form.get("__ajax", None) == "true":
        is_ajax = True

    # Process Form Data
    print("=== Form Data ===")
    for key, value in form.items():
        print(key, "=>", value)

    # Register/Find user and Clean Form Data
    email = ''.join(form["email"].split())
    email = re.sub("[^@\.\w\s\+]", '', email)
    phone = re.sub("[^0-9+]", "", form["phone"])
    name = re.sub("[^\w\s]", '', form['name'])
    gauge_id = None
    if 'gauge_id' in form:
        gauge_id = re.sub("[^\w\s]", '', form['gauge_id']).lower()
    #  Clean / Validate Email
    if len(email) == 0 or '@' not in email or '.' not in email:
        error = "ERROR: Invalid Email: {}".format(email)
        if is_ajax:
            return ajax_response(False, error)
        else:
            return error

    # Clean / Validate Phone
    phone_digits = re.sub("[^0-9]", "", form["phone"])
    if len(phone) > 0:
        error = ""
        if len(phone_digits) < 10:
            error = "ERROR: Invalid Phone, need at least 10 digits"
        elif len(phone_digits) > 13:
            error = "ERROR: Invalid Phone, too many digits"
        if len(error) > 0:
            if is_ajax:
                return ajax_response(False, error)
            else:
                return error

    ajax_status = False
    message = "Existing User Found: {} ".format(email)
    # Check if user exists or phone needs update
    try:
        user = User.get(User.email == email)
    except User.DoesNotExist:
        print("New User: {}".format(email))
        ajax_status = True
        message = "New User Created: {}.".format(email)
        user = User.create(realname=name, email=email, phone=phone)
    if len(phone) > 0 and (len(user.phone) == 0 or user.phone != phone):
        user.phone = phone
        user.updated = datetime.datetime.utcnow()
        user.save()

    # Assign SmartGauge
    time_now = datetime.datetime.utcnow()
    # Search for open smart gauge assignments
    open_gauge_assigns = SmartGaugeUser.select().where((SmartGaugeUser.gauge_id == gauge_id) &
                                                       (SmartGaugeUser.end_date == None))
    # close all current gauge assignments
    for gauge_assign in open_gauge_assigns:
        gauge_assign.end_date = time_now
        gauge_assign.save()

    # create new gauge assignments
    smartgauge = SmartGaugeUser.create(user=user, gauge_id=gauge_id)
    message += "and SmartGauge {} assigned ".format(gauge_id)

    if is_ajax:
        return ajax_response(ajax_status, message)
    else:
        return redirect(url_for("register_user_get"))


@app.route('/assign_gauge', methods=['GET'])
def assign_gauge_get():
    users = User.select()

    return render_template("assign_gauge.html", users=users)


@app.route('/assign_gauge', methods=['POST'])
def assign_gauge_post():
    form = request.form
    # Is the upload using Ajax, or a direct POST by the form?
    is_ajax = False
    if form.get("__ajax", None) == "true":
        is_ajax = True

    # Process Form Data
    print("=== Form Data ===")
    for key, value in form.items():
        print(key, "=>", value)

    # Register/Find user and Clean Form Data
    user_id = int(form['user_id'])
    gauge_id = gauge_id = re.sub("[^\w\s]", '', form['gauge_id']).lower()

    # Assign SmartGauge
    time_now = datetime.datetime.utcnow()
    # Search for open smart gauge assignments
    open_gauge_assigns = SmartGaugeUser.select().where((SmartGaugeUser.gauge_id == gauge_id) &
                                                       (SmartGaugeUser.end_date == None))
    # close all current gauge assignments
    for gauge_assign in open_gauge_assigns:
        gauge_assign.end_date = time_now
        gauge_assign.save()

    # Check if user exists
    try:
        user = User.get(User.id == user_id)
    except User.DoesNotExist:
        error = "ERROR: Invalid user"
        if is_ajax:
            return ajax_response(False, error)
        else:
            return error

    # create new gauge assignments
    smartgauge = SmartGaugeUser.create(user=user, gauge_id=gauge_id)
    message = "User {} assigned SmartGauge {}".format(user.realname, gauge_id)

    if is_ajax:
        return ajax_response(True, message)
    else:
        return redirect(url_for("assign_gauge_get"))


@app.route("/view_day/<int:user_id>/<date_str>/")
@app.route("/view_day/<int:user_id>/<date_str>/<int:datalog_id>/")
def view_day(user_id, date_str, datalog_id=None):

    date_start = datetime.datetime.strptime(date_str, '%m-%d-%Y')
    # Currently assuming PST timezone
    date_start = date_start + datetime.timedelta(hours=8)
    date_end = date_start + datetime.timedelta(hours=23, minutes=59, seconds=59)
    print("date start: {}, end:{}".format(date_start, date_end))

    try:
        datalogs = DataLog.select().join(User).switch(DataLog).join(Activity).switch(DataLog).join(DataLogDoarama).where((DataLog.user == user_id) &
            (DataLog.performed >= date_start) & (DataLog.performed <= date_end)).order_by(+DataLog.performed)
    except peewee.DoesNotExist:
        return "Error: Does Not Exist"

    if not datalogs.count():
        return "Error: No sessions found"

    # If no datalog_id specified, use latest
    datalog_list = []
    for session_num, datalog in enumerate(datalogs):
        datalog.session_num = session_num + 1
        if datalog.racecourse:
            datalog.racecourse.get()
            # Find Laps
            try:
                laps = datalog.Laps.select().where(datalog == datalog)
            except peewee.DoesNotExist:
                laps = None
            datalog.laps = []
            for lap in laps:
                if lap.is_fastest_time:
                    fastest_lap = lap
                datalog.laps.append(lap)
        else:
            datalog.laps = None
        # Find Doarama's
        try:
            datalog.doarama = datalog.Doaramas.get().doarama
        except peewee.DoesNotExist:
            return "Error:Doarama Does Not Exist"
        datalog_list.append(datalog)
        if datalog.id == datalog_id:
            datalog_match = datalog
        print('Found Log: {d.id}, activity:{d.activity.name}'.format(d=datalog))

    # If datalog_id specified, use that one
    if 'datalog_match' in locals():
        datalog = datalog_match

    # Get name
    if datalog.user.realname:
        name = datalog.user.realname
    else:
        name = datalog.user.email.split('@')[0]

    # Get fastest lap speed gate points
    points = Point.select().where(Point.lap == fastest_lap.id).order_by(+Point.time)
    speedgate_points = []
    for point in points:
        speedgate_points.append(point)

    # Get fastest lap split times
    fastest_lap_splits = Split.select().where(Split.lap == fastest_lap.id).order_by(+Split.id)
    '''
    fastest_lap_splits = []
    for split in splits:
        fastest_lap_splits.append(split)
    '''

    # Get ProCompare Images
    procompare_files = []
    if datalog.racecourse:
        filepath = os.path.join(datalog.filepath, 'procompare')
        if not os.path.isdir(filepath):
            print("ProCompare folder not found")
        else:
            for file in glob.glob("{}/*.jpg".format(filepath)):
                filename = os.path.relpath(file, BASE_DIR)
                filename = urllib.parse.quote(filename, safe='/\\')
                procompare_files.append('/'+filename)

    return render_template("view_day.html", datalog=datalog, datalog_list=datalog_list,
                           vis_key=datalog.doarama.visual_key, name=name,
                           race_course=datalog.racecourse, date=date_start, procompare_files=procompare_files,
                           fastest_lap=fastest_lap, speedgate_points=speedgate_points, fastest_lap_splits=fastest_lap_splits,
                           DOARAMA_BASEURL=DOARAMA_BASEURL, GOOGLE_ANALYTICS_ID=GOOGLE_ANALYTICS_ID, PUSH_APP_URL=PUSH_APP_URL
                           )

@app.route("/view/<int:doarama_id>")
def view_vis(doarama_id):

    try:
        datalog_doarama = DataLogDoarama.select().join(Doarama).switch(DataLogDoarama).join(DataLog)\
            .where(Doarama.id == doarama_id).get()
    except peewee.DoesNotExist:
        return "Error: Does Not Exist"

    datalog = datalog_doarama.datalog
    name = datalog.user.email.split('@')[0]

    if datalog.racecourse:
        datalog.racecourse.get()
        # Find Laps
        laps = datalog.Laps.select().where(datalog == datalog)
        lap_times = []
        for lap in laps:
            lap_times.append(lap)
    else:
        lap_times = None

    return render_template("view_vis.html", vis_key=datalog_doarama.doarama.visual_key, name=name,
                           race_course=datalog.racecourse, lap_times=lap_times)


@app.before_request
def before_request():
    g.db = db
    g.db.connect()

    g.FACEBOOK_APP_ID = FACEBOOK_APP_ID


@app.after_request
def after_request(response):
    if not g.db.is_closed():
        g.db.close()
    return response


def ajax_response(status, msg):
    status_code = "ok" if status else "error"
    return json.dumps(dict(
        status=status_code,
        msg=msg,
    ))


def allowed_file(filename):
    return '.' in filename and \
           (filename.rsplit('.', 1)[1]).lower() in ALLOWED_EXTENSIONS


def set_local_development_flag():
    # Flag for local development
    global LOCAL_DEVELOPMENT
    LOCAL_DEVELOPMENT = True
