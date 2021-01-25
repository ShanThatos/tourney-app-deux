from extensions import db, random_password
from sqlalchemy import Column, Integer, Text, Boolean, Date, ForeignKey, Table, UniqueConstraint, TIMESTAMP
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import relationship, backref

class Coach(db.Model):
    __tablename__ = "coaches"
    id = Column(Integer, primary_key=True)
    name = Column(Text, nullable=False)
    phone = Column(Text, nullable=False)
    email = Column(Text, unique=True, nullable=False)
    password = Column(Text, nullable=False)
    admin = Column(Boolean, default=False, nullable=False)
    school_name = Column(Text, nullable=False)
    stripe_id = Column(Text, unique=True)
    students = relationship("Student", backref="coach", lazy="dynamic")
    owned_tourneys = relationship("Tourney", backref="owner", lazy="dynamic")
    collabs_tourneys = relationship("Tourney", secondary="tourneycollabs", lazy="dynamic")
    attending_tourneys = relationship("Tourney", secondary="tourneycoach", lazy="dynamic")

    def __init__(self, args):
        self.name = args[0]
        self.email = args[1]
        self.phone = args[2]
        self.school_name = args[3]
        self.password = args[4]

class Student(db.Model):
    __tablename__ = "students"
    id = Column(Integer, primary_key=True)
    first_name = Column(Text, nullable=False)
    last_name = Column(Text, nullable=False)
    grade = Column(Integer, nullable=False)
    coach_id = Column(Integer, ForeignKey("coaches.id"), nullable=False)
    school_id = Column(Integer, ForeignKey("schools.id"))
    tourneys = relationship("Tourney", secondary="tourneystudent", lazy="dynamic")

    def __init__(self, args):
        self.first_name = args[0]
        self.last_name = args[1]
        self.grade = args[2]
        self.coach_id = args[3]

class Tourney(db.Model):
    __tablename__ = "tourneys"
    id = Column(Integer, primary_key=True)
    date = Column(Date, nullable=False)
    close_date = Column(TIMESTAMP, nullable=False)
    min_grade = Column(Integer, nullable=False)
    max_grade = Column(Integer, nullable=False)
    info = Column(JSONB, nullable=False)
    coach_id = Column(Integer, ForeignKey("coaches.id"), nullable=False)
    collaborators = relationship("Coach", secondary="tourneycollabs", lazy="dynamic")
    coaches = relationship("Coach", secondary="tourneycoach", lazy="dynamic")
    students = relationship("Student", secondary="tourneystudent", lazy="dynamic")
    data_entry_accounts = relationship("DataEntry", backref="tourney", lazy="dynamic")
    def update(self, args):
        self.date = args["date"]
        self.close_date = args["close_date"]
        self.min_grade = args["min_grade"]
        self.max_grade = args["max_grade"]
        self.info = args["info"]
    def __init__(self, args):
        self.coach_id = args["coach_id"]
        self.update(args)

class TourneyCoach(db.Model):
    __tablename__ = "tourneycoach"
    id = Column(Integer, primary_key=True)
    tourney_id = Column(Integer, ForeignKey("tourneys.id"), nullable=False)
    coach_id = Column(Integer, ForeignKey("coaches.id"), nullable=False)
    paid = Column(Boolean, default=False, nullable=False)
    comments = Column(Text, default="", nullable=False)
    coach = relationship("Coach", backref=backref("tourneycoach", cascade="all, delete-orphan"))
    tourney = relationship("Tourney", backref=backref("tourneycoach", cascade="all, delete-orphan"))
    __table_args__ = (UniqueConstraint("tourney_id", "coach_id", name="tc_constraint"),)

class TourneyStudent(db.Model):
    __tablename__ = "tourneystudent"
    id = Column(Integer, primary_key=True)
    tourney_id = Column(Integer, ForeignKey("tourneys.id"), nullable=False)
    student_id = Column(Integer, ForeignKey("students.id"), nullable=False)
    taking_test = Column(Boolean, default=True, nullable=False)
    test = Column(Text, nullable=False)
    score = Column(Integer)
    tie = Column(Text, default="A", nullable=False)
    reg_status = Column(Text, nullable=False)
    student = relationship("Student", backref=backref("tourneystudent", cascade="all, delete-orphan"))
    tourney = relationship("Tourney", backref=backref("tourneystudent", cascade="all, delete-orphan"))
    __table_args__ = (UniqueConstraint("tourney_id", "student_id", name="ts_constraint"),)

class TourneyCollabs(db.Model):
    __tablename__ = "tourneycollabs"
    id = Column(Integer, primary_key=True)
    tourney_id = Column(Integer, ForeignKey("tourneys.id"), nullable=False)
    coach_id = Column(Integer, ForeignKey("coaches.id"), nullable=False)
    tourney = relationship("Tourney", backref=backref("tourneycollabs", cascade="all, delete-orphan"))
    coach = relationship("Coach", backref=backref("tourneycollabs", cascade="all, delete-orphan"))
    __table_args__ = (UniqueConstraint("tourney_id", "coach_id", name="tcollab_constraint"),)

class DataEntry(db.Model):
    __tablename__ = "dataentry"
    id = Column(Integer, primary_key=True)
    tourney_id = Column(Integer, ForeignKey("tourneys.id"), nullable=False)
    username = Column(Text, unique=True, nullable=False)
    password = Column(Text, nullable=False)
    
    def __init__(self, username, tourney_id):
        self.username = username
        self.tourney_id = tourney_id
        self.password = random_password(6)

class School(db.Model):
    __tablename__ = "schools"
    id = Column(Integer, primary_key=True)
    name = Column(Text, unique=True, nullable=False)
    students = relationship("Student", backref="school", lazy="dynamic")

class Order(db.Model):
    __tablename__ = "orders"
    id = Column(Integer, primary_key=True)
    name = Column(Text, nullable=False)
    session_id = Column(Text, unique=True, nullable=False)
    info = Column(JSONB)