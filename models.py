from extensions import db
from sqlalchemy import Column, Integer, Text, Boolean, Date, JSON, ForeignKey, Table, UniqueConstraint
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
    students = relationship("Student", backref="coach")
    owned_tourneys = relationship("Tourney", backref="coach")
    attending_tourneys = relationship("Tourney", secondary="tourneycoach")

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
    tourneys = relationship("Tourney", secondary="tourneystudent")

    def __init__(self, args):
        self.first_name = args[0]
        self.last_name = args[1]
        self.grade = args[2]
        self.coach_id = args[3]

class Tourney(db.Model):
    __tablename__ = "tourneys"
    id = Column(Integer, primary_key=True)
    date = Column(Date, nullable=False)
    close_date = Column(Date)
    min_grade = Column(Integer, nullable=False)
    max_grade = Column(Integer, nullable=False)
    info = Column(JSON, nullable=False)
    coach_id = Column(Integer, ForeignKey("coaches.id"), nullable=False)
    coaches = relationship("Coach", secondary="tourneycoach")
    students = relationship("Student", secondary="tourneystudent")

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
