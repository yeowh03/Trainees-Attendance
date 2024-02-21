from flask import Flask, jsonify, request
from flask.helpers import send_from_directory
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import func
from sqlalchemy.exc import PendingRollbackError, OperationalError, InternalError
import datetime
from flask_marshmallow import Marshmallow
from flask_cors import CORS, cross_origin
import pytz

app = Flask(__name__, static_folder="frontend/build", static_url_path="")
CORS(app)

app.config["SQLALCHEMY_DATABASE_URI"] = \
    "postgresql://postgres.bmgcwuoxqcpnsgfsuyzt:3Hu#E9#*-7ey!Wu@aws-0-ap-southeast-1.pooler.supabase.com:5432/postgres"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

db = SQLAlchemy(app)
app.app_context().push()
ma = Marshmallow(app)

class Recruits(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(200))
    platoon = db.Column(db.Integer)
    esi = db.Column(db.Boolean, default=False)
    rso = db.Column(db.Boolean, default=False)
    esi_back = db.Column(db.Boolean, default=True)
    leave = db.relationship("Leave", backref="recruits")
    remark = db.relationship("Remark", backref="recruits")
    timeoff = db.relationship("TimeOff", backref="recruits")

    def __init__(self, id, name, platoon):
        self.id = id
        self.name = name
        self.platoon = platoon

class Leave(db.Model):
    leave_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    id = db.Column(db.Integer, db.ForeignKey("recruits", ondelete="CASCADE"))
    type = db.Column(db.String(300))
    startDate = db.Column(db.Date)
    endDate = db.Column(db.Date)
    duration = db.Column(db.Integer)
    inCamp = db.Column(db.Boolean)
    active = db.Column(db.Boolean)

    def __init__(self, id, type, startDate, endDate, duration, inCamp, active):
        self.id = id
        self.type = type
        self.startDate = startDate
        self.endDate = endDate
        self.duration = duration
        self.inCamp = inCamp
        self.active = active

class Remark(db.Model):
    remark_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    id = db.Column(db.Integer, db.ForeignKey("recruits", ondelete="CASCADE"))
    remark = db.Column(db.String(300))

    def __init__(self, id, remark):
        self.id = id
        self.remark = remark

class TimeOff(db.Model):
    timeoff_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    id = db.Column(db.Integer, db.ForeignKey("recruits", ondelete="CASCADE"))
    datetimeOut = db.Column(db.DateTime)
    datetimeIn = db.Column(db.DateTime)

    def __init__(self, id, datetimeOut):
        self.id = id
        self.datetimeOut = datetimeOut

class RecruitSchema(ma.Schema):
    class Meta:
        fields = ("id","name","platoon","esi","rmj","rso","esi_back")

class LeaveSchema(ma.Schema):
    class Meta:
        fields = ("leave_id","id","type","startDate","endDate","duration","inCamp","active", "name","platoon")

class RemarkSchema(ma.Schema):
    class Meta:
        fields = ("remark_id","id","remark","name","platoon")

class TimeOffSchema(ma.Schema):
    class Meta:
        fields = ("timeoff_id","id","datetimeOut","datetimeIn", "name","platoon")

db.create_all()
Recruit_Schema = RecruitSchema()
Recruits_Schema = RecruitSchema(many=True)

Leave_Schema = LeaveSchema()
Leaves_Schema = LeaveSchema(many=True)

Remark_Schema = RemarkSchema()
Remarks_Schema = RemarkSchema(many=True)

TimeOff_Schema = TimeOffSchema()
TimeOffs_Schema = TimeOffSchema(many=True)

@app.errorhandler(404)
def not_found(e):
    return send_from_directory(app.static_folder, "index.html")

@app.route("/")
@cross_origin()
def serve():
    return send_from_directory(app.static_folder, "index.html")

@app.route("/add_mc", methods=["POST"])
@cross_origin()
def add_mc():
    # to escape server closure issue due to inactivity
    try:
        rec = Recruits.query.get(1301)
    except:
        db.session.rollback()

    id = request.json["id"]
    startDate=request.json["startDate"]
    endDate=request.json["endDate"]
    type=request.json["type"]

    startYear, startMonth, startDay = startDate.split("-")
    endYear, endMonth, endDay = endDate.split("-")

    start_obj = datetime.date(int(startYear), int(startMonth), int(startDay))
    end_obj = datetime.date(int(endYear), int(endMonth), int(endDay))
    delta = end_obj-start_obj
    duration=delta.days+1

    print("id:", id)

    rec = Recruits.query.get(int(id))
    rec.rso = False
    db.session.commit()

    if not db.session.query(Leave.leave_id).filter(Leave.id==int(id), Leave.startDate==start_obj, Leave.endDate==end_obj, Leave.type==type).all(): # check if entry is already added already to prevent duplicates
        leave = Leave(int(id), "MC", startDate, endDate, duration, False, False)

        db.session.add(leave)
        db.session.commit()
    else:
        print("ALREADY ADDED!!")
    
    return id

@app.route("/get_mc", methods=["GET"])
@cross_origin()
def get_mc():
    # to escape server closure issue due to inactivity
    try:
        rec = Recruits.query.get(1301)
    except:
        db.session.rollback()

    tz = pytz.timezone("Asia/Singapore")
    curr = datetime.datetime.now(tz)
    today_date = curr.date()

    results = db.session.query(Leave.leave_id, Leave.startDate, Leave.endDate, Leave.id, Recruits.name, Recruits.platoon)\
        .join(Recruits,Leave.id==Recruits.id).filter(Leave.type=="MC", Leave.endDate >= today_date).all()
    print(results)
    results = Leaves_Schema.dump(results)
    return jsonify(results)

@app.route("/edit_mc", methods=["PUT"])
@cross_origin()
def edit_mc():
    # to escape server closure issue due to inactivity
    try:
        rec = Recruits.query.get(1301)
    except:
        db.session.rollback()

    leave_id=request.json["leave_id"]
    startDate=request.json["startDate"]
    endDate=request.json["endDate"]
    id = request.json["id"]

    leave = Leave.query.get(leave_id)

    startYear, startMonth, startDay = startDate.split("-")
    endYear, endMonth, endDay = endDate.split("-")

    start_obj = datetime.date(int(startYear), int(startMonth), int(startDay))
    end_obj = datetime.date(int(endYear), int(endMonth), int(endDay))
    delta = end_obj-start_obj
    duration=delta.days+1
    
    leave.startDate = start_obj
    leave.endDate = end_obj
    leave.id = int(id)
    leave.duration = duration

    db.session.commit()

    return id

@app.route("/delete_mc", methods=["DELETE"])
@cross_origin()
def delete_mc():
    # to escape server closure issue due to inactivity
    try:
        rec = Recruits.query.get(1301)
    except:
        db.session.rollback()
        
    leave_id=request.json["leave_id"]
    leave = Leave.query.get(leave_id)
    db.session.delete(leave)
    db.session.commit()

    return str(leave_id)

@app.route("/get_ld", methods=["GET"])
@cross_origin()
def get_ld():
    # to escape server closure issue due to inactivity
    try:
        rec = Recruits.query.get(1301)
    except:
        db.session.rollback()

    tz = pytz.timezone("Asia/Singapore")
    curr = datetime.datetime.now(tz)
    today_date = curr.date()
        
    results = db.session.query(Leave.leave_id, Leave.startDate, Leave.endDate, Leave.id, Recruits.name, Recruits.platoon)\
        .join(Recruits,Leave.id==Recruits.id).filter(Leave.type=="LD", Leave.endDate >= today_date).all()
    print(results)
    results = Leaves_Schema.dump(results)
    return jsonify(results)

@app.route("/add_ld", methods=["POST"])
@cross_origin()
def add_ld():
    # to escape server closure issue due to inactivity
    try:
        rec = Recruits.query.get(1301)
    except:
        db.session.rollback()
        
    id = request.json["id"]
    startDate=request.json["startDate"]
    endDate=request.json["endDate"]
    type=request.json["type"]

    startYear, startMonth, startDay = startDate.split("-")
    endYear, endMonth, endDay = endDate.split("-")

    start_obj = datetime.date(int(startYear), int(startMonth), int(startDay))
    end_obj = datetime.date(int(endYear), int(endMonth), int(endDay))
    delta = end_obj-start_obj
    duration=delta.days+1

    if not db.session.query(Leave.leave_id).filter(Leave.id==int(id), Leave.startDate==start_obj, Leave.endDate==end_obj, Leave.type==type).all(): # check if entry is already added already to prevent duplicates
        leave = Leave(int(id), "LD", startDate, endDate, duration, True, False)

        db.session.add(leave)
        db.session.commit()
    else:
        print("ALREADY ADDED!!")
    
    return id

@app.route("/edit_ld", methods=["PUT"])
@cross_origin()
def edit_ld():
    # to escape server closure issue due to inactivity
    try:
        rec = Recruits.query.get(1301)
    except:
        db.session.rollback()
        
    leave_id=request.json["leave_id"]
    startDate=request.json["startDate"]
    endDate=request.json["endDate"]
    id = request.json["id"]

    leave = Leave.query.get(leave_id)

    startYear, startMonth, startDay = startDate.split("-")
    endYear, endMonth, endDay = endDate.split("-")

    start_obj = datetime.date(int(startYear), int(startMonth), int(startDay))
    end_obj = datetime.date(int(endYear), int(endMonth), int(endDay))
    delta = end_obj-start_obj
    duration=delta.days+1
    
    leave.startDate = start_obj
    leave.endDate = end_obj
    leave.id = int(id)
    leave.duration = duration

    db.session.commit()

    return id

@app.route("/delete_ld", methods=["DELETE"])
@cross_origin()
def delete_ld():
    # to escape server closure issue due to inactivity
    try:
        rec = Recruits.query.get(1301)
    except:
        db.session.rollback()
        
    leave_id=request.json["leave_id"]
    leave = Leave.query.get(leave_id)
    db.session.delete(leave)
    db.session.commit()

    return str(leave_id)

@app.route("/get_rmj", methods=["GET"])
@cross_origin()
def get_rmj():
    # to escape server closure issue due to inactivity
    try:
        rec = Recruits.query.get(1301)
    except:
        db.session.rollback()

    tz = pytz.timezone("Asia/Singapore")
    curr = datetime.datetime.now(tz)
    today_date = curr.date()
        
    results = db.session.query(Leave.leave_id, Leave.startDate, Leave.endDate, Leave.id, Recruits.name, Recruits.platoon)\
        .join(Recruits,Leave.id==Recruits.id).filter(Leave.type=="RMJ", Leave.endDate >= today_date).all()
    print(results)
    results = Leaves_Schema.dump(results)
    return jsonify(results)

@app.route("/add_rmj", methods=["POST"])
@cross_origin()
def add_rmj():
    # to escape server closure issue due to inactivity
    try:
        rec = Recruits.query.get(1301)
    except:
        db.session.rollback()
        
    id = request.json["id"]
    startDate=request.json["startDate"]
    endDate=request.json["endDate"]
    type=request.json["type"]

    startYear, startMonth, startDay = startDate.split("-")
    endYear, endMonth, endDay = endDate.split("-")

    start_obj = datetime.date(int(startYear), int(startMonth), int(startDay))
    end_obj = datetime.date(int(endYear), int(endMonth), int(endDay))
    delta = end_obj-start_obj
    duration=delta.days+1

    if not db.session.query(Leave.leave_id).filter(Leave.id==int(id), Leave.startDate==start_obj, Leave.endDate==end_obj, Leave.type==type).all(): # check if entry is already added already to prevent duplicates
        leave = Leave(int(id), "RMJ", startDate, endDate, duration, True, True)

        db.session.add(leave)
        db.session.commit()
    else:
        print("ALREADY ADDED!!")
    
    return id

@app.route("/edit_rmj", methods=["PUT"])
@cross_origin()
def edit_rmj():
    # to escape server closure issue due to inactivity
    try:
        rec = Recruits.query.get(1301)
    except:
        db.session.rollback()
        
    leave_id=request.json["leave_id"]
    startDate=request.json["startDate"]
    endDate=request.json["endDate"]
    id = request.json["id"]

    leave = Leave.query.get(leave_id)

    startYear, startMonth, startDay = startDate.split("-")
    endYear, endMonth, endDay = endDate.split("-")

    start_obj = datetime.date(int(startYear), int(startMonth), int(startDay))
    end_obj = datetime.date(int(endYear), int(endMonth), int(endDay))
    delta = end_obj-start_obj
    duration=delta.days+1
    
    leave.startDate = start_obj
    leave.endDate = end_obj
    leave.id = int(id)
    leave.duration = duration

    db.session.commit()

    return id

@app.route("/delete_rmj", methods=["DELETE"])
@cross_origin()
def delete_rmj():
    # to escape server closure issue due to inactivity
    try:
        rec = Recruits.query.get(1301)
    except:
        db.session.rollback()
        
    leave_id=request.json["leave_id"]
    leave = Leave.query.get(leave_id)
    db.session.delete(leave)
    db.session.commit()

    return str(leave_id)

@app.route("/get_rso", methods=["GET"])
@cross_origin()
def get_rso():
    # to escape server closure issue due to inactivity
    try:
        rec = Recruits.query.get(1301)
    except:
        db.session.rollback()
        
    results = db.session.query(Recruits.name, Recruits.id, Recruits.platoon).filter(Recruits.rso).all()
    print(results)
    results = Recruits_Schema.dump(results)
    return jsonify(results)

@app.route("/edit_rso", methods=["PUT"])
@cross_origin()
def edit_rso():
    # to escape server closure issue due to inactivity
    try:
        rec = Recruits.query.get(1301)
    except:
        db.session.rollback()
        
    id = request.json["id"]
    rec = Recruits.query.get(int(id))
    rec.rso = not rec.rso
    db.session.commit()

    return str(id)

@app.route("/add_rso", methods=["PUT"])
@cross_origin()
def add_rso():
    # to escape server closure issue due to inactivity
    try:
        rec = Recruits.query.get(1301)
    except:
        db.session.rollback()
        
    id = request.json["id"]
    rec = Recruits.query.get(int(id))
    rec.rso = True
    db.session.commit()

    return str(id)

@app.route("/add_to", methods=["POST"])
@cross_origin()
def add_to():
    # to escape server closure issue due to inactivity
    try:
        rec = Recruits.query.get(1301)
    except:
        db.session.rollback()
        
    id = request.json["id"]

    timeoff = TimeOff(int(id), datetime.datetime.now())

    db.session.add(timeoff)
    db.session.commit()
   
    return str(id)

@app.route("/edit_to", methods=["PUT"])
@cross_origin()
def edit_to():
    # to escape server closure issue due to inactivity
    try:
        rec = Recruits.query.get(1301)
    except:
        db.session.rollback()
        
    timeoff_id = request.json["timeoff_id"]
    to = TimeOff.query.get(int(timeoff_id))
    to.datetimeIn = datetime.datetime.now()
    db.session.commit()

    return str(timeoff_id)

@app.route("/delete_to", methods=["DELETE"])
@cross_origin()
def delete_to():
    # to escape server closure issue due to inactivity
    try:
        rec = Recruits.query.get(1301)
    except:
        db.session.rollback()
        
    timeoff_id=request.json["timeoff_id"]
    to = TimeOff.query.get(int(timeoff_id))
    db.session.delete(to)
    db.session.commit()

    return str(timeoff_id)

@app.route("/get_to", methods=["GET"])
@cross_origin()
def get_to():
    # to escape server closure issue due to inactivity
    try:
        rec = Recruits.query.get(1301)
    except:
        db.session.rollback()
        
    results = db.session.query(Recruits.name, Recruits.id, TimeOff.timeoff_id, Recruits.platoon).join(TimeOff, Recruits.id==TimeOff.id).filter(TimeOff.datetimeIn==None).all()
    print(results, "ABCS")
    results = TimeOffs_Schema.dump(results)
    return jsonify(results)

@app.route("/get_others", methods=["GET"])
@cross_origin()
def get_others():
    # to escape server closure issue due to inactivity
    try:
        rec = Recruits.query.get(1301)
    except:
        db.session.rollback()

    tz = pytz.timezone("Asia/Singapore")
    curr = datetime.datetime.now(tz)
    today_date = curr.date()
        
    results = db.session.query(Leave.leave_id, Leave.startDate, Leave.endDate, Leave.id, Leave.type, Recruits.name, Leave.inCamp, Leave.active, Recruits.platoon)\
        .join(Recruits,Leave.id==Recruits.id).filter(Leave.type!="RMJ", Leave.type!="MC", Leave.type!="LD", Leave.endDate >= today_date).all()
    print(results)
    results = Leaves_Schema.dump(results)
    return jsonify(results)

@app.route("/add_others", methods=["POST"])
@cross_origin()
def add_others():
    # to escape server closure issue due to inactivity
    try:
        rec = Recruits.query.get(1301)
    except:
        db.session.rollback()
        
    id = request.json["id"]
    startDate=request.json["startDate"]
    endDate=request.json["endDate"]
    type=request.json["type"]
    inCamp=request.json["inCamp"]
    active=request.json["active"]

    startYear, startMonth, startDay = startDate.split("-")
    endYear, endMonth, endDay = endDate.split("-")

    start_obj = datetime.date(int(startYear), int(startMonth), int(startDay))
    end_obj = datetime.date(int(endYear), int(endMonth), int(endDay))
    delta = end_obj-start_obj
    duration=delta.days+1

    if not db.session.query(Leave.leave_id).filter(Leave.id==int(id), Leave.startDate==start_obj, Leave.endDate==end_obj, Leave.type==type).all(): # check if entry is already added already to prevent duplicates
        leave = Leave(int(id), type, startDate, endDate, duration, inCamp, active)
        db.session.add(leave)
        db.session.commit()
    else:
        print("ALREADY ADDED!!")
    
    return id

@app.route("/edit_others", methods=["PUT"])
@cross_origin()
def edit_others():
    # to escape server closure issue due to inactivity
    try:
        rec = Recruits.query.get(1301)
    except:
        db.session.rollback()
        
    id = request.json["id"]
    startDate=request.json["startDate"]
    endDate=request.json["endDate"]
    type=request.json["type"]
    inCamp=request.json["inCamp"]
    active=request.json["active"]
    leave_id=request.json["leave_id"]

    leave = Leave.query.get(leave_id)

    startYear, startMonth, startDay = startDate.split("-")
    endYear, endMonth, endDay = endDate.split("-")

    start_obj = datetime.date(int(startYear), int(startMonth), int(startDay))
    end_obj = datetime.date(int(endYear), int(endMonth), int(endDay))
    delta = end_obj-start_obj
    duration=delta.days+1
    
    leave.startDate = start_obj
    leave.endDate = end_obj
    leave.id = int(id)
    leave.duration = duration
    leave.type = type
    leave.inCamp = inCamp
    leave.active = active

    db.session.commit()

    return id

@app.route("/delete_others", methods=["DELETE"])
@cross_origin()
def delete_others():
    # to escape server closure issue due to inactivity
    try:
        rec = Recruits.query.get(1301)
    except:
        db.session.rollback()
        
    leave_id=request.json["leave_id"]
    leave = Leave.query.get(leave_id)
    db.session.delete(leave)
    db.session.commit()

    return str(leave_id)

@app.route("/get_remarks", methods=["GET"])
@cross_origin()
def get_remarks():
    # to escape server closure issue due to inactivity
    try:
        rec = Recruits.query.get(1301)
    except:
        db.session.rollback()
        
    results = db.session.query(Recruits.name, Recruits.id, Remark.remark_id, Remark.remark, Recruits.platoon).join(Remark, Recruits.id==Remark.id).all()
    print(results, "Remarks sent!!!!")
    results = Remarks_Schema.dump(results)
    return jsonify(results)

@app.route("/add_remarks", methods=["POST"])
@cross_origin()
def add_remarks():
    # to escape server closure issue due to inactivity
    try:
        rec = Recruits.query.get(1301)
    except:
        db.session.rollback()
        
    id = request.json["id"]
    remark=request.json["remark"]

    remark_obj = Remark(int(id), remark)

    db.session.add(remark_obj)
    db.session.commit()
    
    return id

@app.route("/edit_remarks", methods=["PUT"])
@cross_origin()
def edit_remarks():
    # to escape server closure issue due to inactivity
    try:
        rec = Recruits.query.get(1301)
    except:
        db.session.rollback()
        
    id = request.json["id"]
    remark_id=request.json["remark_id"]
    remark=request.json["remark"]

    remark_obj = Remark.query.get(remark_id)

    
    remark_obj.remark = remark
    remark_obj.id = int(id)

    db.session.commit()

    return id

@app.route("/delete_remarks", methods=["DELETE"])
@cross_origin()
def delete_remarks():
    # to escape server closure issue due to inactivity
    try:
        rec = Recruits.query.get(1301)
    except:
        db.session.rollback()
        
    remark_id=request.json["remark_id"]
    remark_obj = Remark.query.get(remark_id)
    db.session.delete(remark_obj)
    db.session.commit()

    return str(remark_id)

@app.route("/get_esi", methods=["GET"])
@cross_origin()
def get_esi():
    # to escape server closure issue due to inactivity
    try:
        rec = Recruits.query.get(1301)
    except:
        db.session.rollback()
        
    results = db.session.query(Recruits.name, Recruits.id, Recruits.esi_back, Recruits.platoon).filter(Recruits.esi).all()
    print(results, "ABCS")
    results = Recruits_Schema.dump(results)
    return jsonify(results)

@app.route("/add_esi", methods=["PUT"])
@cross_origin()
def add_esi():
    # to escape server closure issue due to inactivity
    try:
        rec = Recruits.query.get(1301)
    except:
        db.session.rollback()
        
    id = request.json["id"]
    rec = Recruits.query.get(int(id))
    rec.esi = True
    db.session.commit()
    return str(id)

@app.route("/delete_esi", methods=["PUT"])
@cross_origin()
def delete_esi():
    # to escape server closure issue due to inactivity
    try:
        rec = Recruits.query.get(1301)
    except:
        db.session.rollback()
        
    id = request.json["id"]
    rec = Recruits.query.get(int(id))
    rec.esi = False
    rec.esi_back = True
    db.session.commit()
    return str(id)

@app.route("/esi_entry", methods=["PUT"])
@cross_origin()
def esi_entry():
    # to escape server closure issue due to inactivity
    try:
        rec = Recruits.query.get(1301)
    except:
        db.session.rollback()
        
    id = request.json["id"]
    rec = Recruits.query.get(int(id))
    rec.esi_back = not rec.esi_back
    db.session.commit()
    return str(id)

@app.route("/status", methods=["GET"])
@cross_origin()
def status():
    # to escape server closure issue due to inactivity
    try:
        rec = Recruits.query.get(1301)
    except:
        db.session.rollback()

    tz = pytz.timezone("Asia/Singapore")
    curr = datetime.datetime.now(tz)
    today_date = curr.date()
        
    totalPltOne = Recruits.query.filter(Recruits.platoon==1).count()
    totalPltTwo = Recruits.query.filter(Recruits.platoon==2).count()
    totalPltThree = Recruits.query.filter(Recruits.platoon==3).count()

    abs_leave_1 = db.session.query(Leave.id)\
        .join(Recruits, Recruits.id==Leave.id)\
        .filter(Leave.inCamp==False, Leave.endDate >= today_date, Recruits.platoon==1).all()
    esi_leave_1 = db.session.query(Recruits.id).filter(Recruits.esi_back==False, Recruits.platoon==1).all()
    timeoff_leave_1 = db.session.query(TimeOff.id)\
        .join(Recruits, Recruits.id==TimeOff.id)\
        .filter(TimeOff.datetimeIn==None, Recruits.platoon==1).all()
    rso_leave_1 = db.session.query(Recruits.id).filter(Recruits.rso==True, Recruits.platoon==1).all()
    abs_names_1 = set()
    for name in abs_leave_1:
        abs_names_1.add(name)
    for name in esi_leave_1:
        abs_names_1.add(name)
    for name in timeoff_leave_1:
        abs_names_1.add(name)
    for name in rso_leave_1:
        abs_names_1.add(name)
    currentPltOne = totalPltOne-len(abs_names_1)

    print("abs_names_1", abs_names_1)
    print("currentPltOne", currentPltOne)

    inactive_1 = db.session.query(Leave.id)\
        .join(Recruits, Recruits.id==Leave.id)\
        .filter(Leave.inCamp, Leave.active==False, Recruits.platoon==1, Leave.endDate >= today_date).all()
    activePltOne = currentPltOne
    for name in inactive_1:
        if name not in abs_names_1:
            activePltOne -= 1

    print("activeOne", activePltOne)

    abs_leave_2 = db.session.query(Leave.id)\
        .join(Recruits, Recruits.id==Leave.id)\
        .filter(Leave.inCamp==False, Leave.endDate >= today_date, Recruits.platoon==2).all()
    esi_leave_2 = db.session.query(Recruits.id).filter(Recruits.esi_back==False, Recruits.platoon==2).all()
    timeoff_leave_2 = db.session.query(TimeOff.id)\
        .join(Recruits, Recruits.id==TimeOff.id)\
        .filter(TimeOff.datetimeIn==None, Recruits.platoon==2).all()
    rso_leave_2 = db.session.query(Recruits.id).filter(Recruits.rso==True, Recruits.platoon==2).all()
    abs_names_2 = set()
    for name in abs_leave_2:
        abs_names_2.add(name)
    for name in esi_leave_2:
        abs_names_2.add(name)
    for name in timeoff_leave_2:
        abs_names_2.add(name)
    for name in rso_leave_2:
        abs_names_2.add(name)
    currentPltTwo = totalPltTwo-len(abs_names_2)

    print("abs_names_2", abs_names_2)
    print("currentPltTwo", currentPltTwo)

    inactive_2 = db.session.query(Leave.id)\
        .join(Recruits, Recruits.id==Leave.id)\
        .filter(Leave.inCamp, Leave.active==False, Recruits.platoon==2, Leave.endDate >= today_date).all()
    activePltTwo = currentPltTwo
    for name in inactive_2:
        if name not in abs_names_2:
            activePltTwo -= 1

    print("activeTwo", activePltTwo)

    abs_leave_3 = db.session.query(Leave.id)\
        .join(Recruits, Recruits.id==Leave.id)\
        .filter(Leave.inCamp==False, Leave.endDate >= today_date, Recruits.platoon==3).all()
    esi_leave_3 = db.session.query(Recruits.id).filter(Recruits.esi_back==False, Recruits.platoon==3).all()
    timeoff_leave_3 = db.session.query(TimeOff.id)\
        .join(Recruits, Recruits.id==TimeOff.id)\
        .filter(TimeOff.datetimeIn==None, Recruits.platoon==3).all()
    rso_leave_3 = db.session.query(Recruits.id).filter(Recruits.rso==True, Recruits.platoon==3).all()
    abs_names_3 = set()
    for name in abs_leave_3:
        abs_names_3.add(name)
    for name in esi_leave_3:
        abs_names_3.add(name)
    for name in timeoff_leave_3:
        abs_names_3.add(name)
    for name in rso_leave_3:
        abs_names_3.add(name)
    currentPltThree = totalPltThree-len(abs_names_3)


    print("abs_names_3", abs_names_3)
    print("currentPltThree", currentPltThree)

    inactive_3 = db.session.query(Leave.id)\
        .join(Recruits, Recruits.id==Leave.id)\
        .filter(Leave.inCamp, Leave.active==False, Recruits.platoon==3, Leave.endDate >= today_date).all()
    activePltThree = currentPltThree
    for name in inactive_3:
        if name not in abs_names_3:
            activePltThree -= 1

    print("activeThree", activePltThree)

    company_names = set()
    companyMC = db.session.query(Leave.id).filter(Leave.type=="MC",Leave.endDate >= today_date).all()
    for name in companyMC:
        company_names.add(name[0])
    companyMCCount = len(companyMC)

    company_names_Count = len(company_names)
    companyRSO = db.session.query(Recruits.id).filter(Recruits.rso).all()
    for name in companyRSO:
        company_names.add(name[0])
    companyRSOCount = len(company_names) - company_names_Count

    company_esi_out = db.session.query(Recruits.id).filter(Recruits.esi_back == False).all()
    company_names_Count = len(company_names)
    for name in company_esi_out:
        company_names.add(name[0])
    companyESICount = len(company_names) - company_names_Count

    others_dic = {}
    companyOthersCount = 0
    companyOthers = db.session.query(Leave.id, Leave.type).filter(Leave.inCamp==False, Leave.endDate >= today_date).all()
    for name in companyOthers:
        if name[0] not in company_names:
            company_names.add(name[0])
            if others_dic.get(name[1]) == None:
                others_dic[name[1]] = 1
            else:
                others_dic[name[1]] += 1
            companyOthersCount+=1
    
    timeoff = db.session.query(TimeOff.id).filter(TimeOff.datetimeIn==None).all()
    for name in timeoff:
        if name[0] not in company_names:
            company_names.add(name[0])
            if others_dic.get("TimeOff") == None:
                others_dic["TimeOff"] = 1
            else:
                others_dic["TimeOff"] += 1
            companyOthersCount+=1

    print("companyMCCount", companyMCCount)
    print("companyRSOCount", companyRSOCount)
    print("companyOthersCount", companyOthersCount)
    print("others_dic", others_dic)

    return jsonify([{"totalPltOne": totalPltOne, "totalPltTwo":totalPltTwo, "totalPltThree":totalPltThree, "currentPltOne":currentPltOne, "currentPltTwo":currentPltTwo, "currentPltThree":currentPltThree, \
                     "activePltOne":activePltOne, "activePltTwo":activePltTwo, "activePltThree":activePltThree, "companyMCCount":companyMCCount, "companyRSOCount":companyRSOCount, "companyOthersCount":companyOthersCount, "others_dic":others_dic,\
                        "companyESICount":companyESICount}])

@app.route("/track", methods=["GET"])
def track():
    # to escape server closure issue due to inactivity
    try:
        rec = Recruits.query.get(1301)
    except:
        db.session.rollback()
        
    totalMC = db.session.query(func.sum(Leave.duration).label("duration"), Recruits.name, Leave.id)\
        .join(Recruits, Recruits.id==Leave.id).filter(Leave.type=="MC").group_by(Leave.id, Recruits.name).order_by(func.sum(Leave.duration).desc()).all()
    totalMC = Leaves_Schema.dump(totalMC)
    print(totalMC)
    return jsonify(totalMC)

@app.route("/mc_history", methods=["GET"])
def mc_history():
    # to escape server closure issue due to inactivity
    try:
        rec = Recruits.query.get(1301)
    except:
        db.session.rollback()
    
    history = db.session.query(Leave.id, Leave.startDate, Leave.endDate).filter(Leave.type=="MC").all()
    history = Leaves_Schema.dump(history)
    print("HISTORY", history)
    return jsonify(history)

if __name__ == "__main__":
    app.run()

    
    



