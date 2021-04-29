from datetime import datetime

from v1 import db


user_part = db.Table('users_patriarchs',
                     db.Column('userId', db.Integer, db.ForeignKey('users.useId')),
                     db.Column('partId', db.Integer, db.ForeignKey('patriarchs.partId')),
                     comment='realize the many-to-many between users and patriarchs')

part_stu = db.Table('patriarchs_students',
                    db.Column('partId', db.Integer, db.ForeignKey('patriarchs.partId')),
                    db.Column('stuId', db.Integer, db.ForeignKey('students.stuId')),
                    comment='realize the many-to-many between students and patriarchs')

user_teacher = db.Table('users_teachers',
                        db.Column('useId', db.Integer, db.ForeignKey('users.useId')),
                        db.Column('teaId', db.Integer, db.ForeignKey('teachers.teaId')),
                        comment='realize the many-to-many between users and teacher')

tea_cla = db.Table('teachers_classes',
                   db.Column('teaId', db.Integer, db.ForeignKey('teachers.teaId')),
                   db.Column('classId', db.Integer, db.ForeignKey('classes.classId')),
                   comment='realize the many-to-many between teachers and classes')

tea_sub = db.Table('teachers_subjects',
                   db.Column('teaId', db.Integer, db.ForeignKey('teachers.teaId')),
                   db.Column('subId', db.Integer, db.ForeignKey('subjects.subId')),
                   comment='realize the many-to-many between teachers and subjects')


cla_stu = db.Table('classes_students',
                   db.Column('classId', db.Integer, db.ForeignKey('classes.classId')),
                   db.Column('stuId', db.Integer, db.ForeignKey('students.stuId')),
                   comment='realize the many-to-many between grades and students')

sub_stu = db.Table('subjects_students',
                   db.Column('subId', db.Integer, db.ForeignKey('subjects.subId')),
                   db.Column('stuId', db.Integer, db.ForeignKey('students.stuId')),
                   comment='realize the many-to-many between subjects and students')

stu_opera = db.Table('students_operations',
                     db.Column('stuId', db.Integer, db.ForeignKey('students.stuId')),
                     db.Column('operaId', db.Integer, db.ForeignKey('operations.operaId')),
                     comment='student and homework relationship')


class BaseModel(db.Model):
    """
    Implementation of the basic method and basic fields
    """
    __abstract__ = True

    timeCreate = db.Column(db.DateTime, default=datetime.now, onupdate=datetime.now, comment='updated time')
    timeModified = db.Column(db.DateTime, default=datetime.now, comment=' created time')

    def add(self):
        db.session.add(self)
        db.session.commit()

    def update(self):
        db.session.update(self)
        db.session.commit()

    def delete(self):
        db.session.delete(self)
        db.session.commit()


class Users(BaseModel):
    """
    users are used as basic information tables
    """

    __tablename__ = 'users'

    useId = db.Column(db.Integer, autoincrement=True, primary_key=True, comment='foreign key')
    openId = db.Column(db.String(128), nullable=False, comment='openid')
    username = db.Column(db.String(64), index=True, unique=True, comment='actual name')
    nickname = db.Column(db.String(64), comment='nick name')
    mobile = db.Column(db.String(11), index=True, unique=True, comment='mobile')
    sex = db.Column(db.SmallInteger, comment='sex')
    age = db.Column(db.String(128), comment='age')
    avatar = db.Column(db.String(128), nullable=False)
    isDelete = db.Column(db.Boolean, default=False, comment='whether to logical deletion')
    isActive = db.Column(db.Boolean, default=False, comment='whether to active')
    identifyId = db.Column(db.SmallInteger, comment='whether to judge the user identify')

    part = db.relationship('Patriarchs',
                           secondary=user_part,
                           backref=db.backref('users', lazy='dynamic'),
                           lazy='dynamic')

    teacher = db.relationship('Teachers',
                              secondary=user_teacher,
                              backref=db.backref('users', lazy='dynamic'),
                              lazy='dynamic')

    @classmethod
    def get(cls, openid):
        return cls.query.filter_by(openId=openid).first()


class Patriarchs(BaseModel):
    """
    patriarchs
    """

    __tablename__ = 'patriarchs'

    partId = db.Column(db.Integer, index=True, primary_key=True, comment='foreign key')
    username = db.Column(db.String(128), unique=True, comment='actual name')
    mobile = db.Column(db.String(11), comment='mobile')
    sex = db.Column(db.SmallInteger, comment='sex')
    age = db.Column(db.String(128), comment='age ')
    isHasClass = db.Column(db.Boolean, default=False, comment='whether to add class')
    identifyId = db.Column(db.SmallInteger, comment='whether to judge the user identify')


class Schools(BaseModel):

    """
    schools
    """

    __tablename__ = 'schools'

    schId = db.Column(db.Integer, autoincrement=True, primary_key=True, comment='foreign key')
    schoolName = db.Column(db.String(128), comment='school name')
    schoolCode = db.Column(db.String(255), index=True, unique=True, comment='school identification code')
    educationTypeName = db.Column(db.String(128), comment='school system name')
    periodName = db.Column(db.String(128), comment='school section')
    telephone = db.Column(db.String(11), comment='school telephone')
    grades = db.relationship('Grades', backref="grades", cascade='all')


class Teachers(BaseModel):
    """
    teachers
    """

    __tablename__ = 'teachers'

    teaId = db.Column(db.Integer, autoincrement=True, primary_key=True, comment='foreign key')
    username = db.Column(db.String(128), index=True, unique=True, comment='actual name')
    nickname = db.Column(db.String(64), comment='nick name')
    sex = db.Column(db.SmallInteger, comment='sex')
    mobile = db.Column(db.String(11), index=True, unique=True, comment='mobile')
    age = db.Column(db.String(128))
    avatar = db.Column(db.String(128), comment='avatar')
    isDeleted = db.Column(db.Boolean, default=False, comment='logical deletion')
    isActive = db.Column(db.Boolean, default=False, comment='whether to active')
    isHeadTeacher = db.Column(db.Boolean, default=False, comment='whether to judge headteacher')
    isHasClass = db.Column(db.Boolean, default=False, comment='whether to add class')
    status = db.Column(db.Boolean, default=False, comment='status Whether to become a teacher')
    identifyId = db.Column(db.SmallInteger, comment='whether to judge the user identify')
    operation = db.relationship('Operations', backref='teachers', lazy=True,
                                comment='The relationship between the teacher and the homework')
    subject = db.relationship('Subjects',
                              secondary=tea_sub,
                              backref=db.backref('teachers', lazy='dynamic'),
                              lazy='dynamic')


class Grades(BaseModel):
    """
    grades
    """

    __tablename__ = 'grades'

    graId = db.Column(db.Integer, autoincrement=True, primary_key=True, comment='foreign key')
    gradeCode = db.Column(db.Integer, index=True, unique=True, comment='grade code')
    gradeName = db.Column(db.String(128), unique=True, comment='grade name')
    isGraduate = db.Column(db.Boolean, default=False, comment='whether graduate')
    schId = db.Column(db.Integer, db.ForeignKey('schools.schId'), comment='achieve one-to-many')
    classes = db.relationship('Classes', backref="classes", cascade='all')


class Classes(BaseModel):
    """
    class
    """
    __tablename__ = 'classes'

    classId = db.Column(db.Integer, unique=True, autoincrement=True, primary_key=True, comment='class code')
    className = db.Column(db.String(128), unique=True, comment='class name')
    class_types = db.Column(db.SmallInteger, comment='class types')
    graId = db.Column(db.Integer, db.ForeignKey('grades.graId'), comment='achieve one-to-many')
    status = db.Column(db.SmallInteger, default=False, comment='status　Whether to start classes')
    teachers = db.relationship('Teachers',
                               secondary=tea_cla,
                               backref=db.backref('Classes', lazy='dynamic'),
                               lazy='dynamic')
    students = db.relationship('Students',
                               secondary=cla_stu,
                               backref=db.backref('classes', lazy='dynamic'),
                               lazy='dynamic')


class Subjects(BaseModel):
    """
    subjects
    """

    __tablename__ = 'subjects'

    subId = db.Column(db.Integer, autoincrement=True, primary_key=True, comment='foreign key')
    subjectId = db.Column(db.String(255), index=True, unique=True, comment='subject code')
    subjectName = db.Column(db.String(128), comment='subject name')
    status = db.Column(db.SmallInteger, default=False, comment='status　Whether to start subjects')


class Students(BaseModel):
    """
    students
    """

    __tablename__ = 'students'

    stuId = db.Column(db.Integer, autoincrement=True, primary_key=True, comment='foreign key')
    username = db.Column(db.String(128), index=True, unique=True, comment='actual name')
    nickname = db.Column(db.String(64), comment='nick name')
    sex = db.Column(db.SmallInteger, comment='sex')
    mobile = db.Column(db.String(11), index=True, unique=True, comment='mobile')
    age = db.Column(db.String(128), comment='age')
    avatar = db.Column(db.String(128), nullable=False)
    identifyId = db.Column(db.SmallInteger, comment='whether to judge the user identify')
    isDeleted = db.Column(db.Boolean, default=False, comment='whether logical deletion')
    isActive = db.Column(db.Boolean, default=False, comment='whether to active')
    isHasClass = db.Column(db.Boolean, default=True, comment='whether to add class')
    relatives = db.Column(db.SmallInteger, comment='kinship')
    status = db.Column(db.Boolean, default=False, comment='status Whether to become a student')
    patriarchs = db.relationship('Patriarchs',
                                 secondary=part_stu, backref=db.backref('students', lazy='dynamic'),
                                 lazy='dynamic')
    subjects = db.relationship('Subjects',
                               secondary=sub_stu,
                               backref=db.backref('students', lazy='dynamic'),
                               lazy='dynamic')
    operation = db.relationship('Operations', secondary=stu_opera,
                                backref=db.backref('students', lazy='dynamic'), lazy='dynamic')


class Operations(BaseModel):
    """
    operation
    """

    __tablename__ = 'operations'
    operaId = db.Column(db.Integer, autoincrement=True, primary_key=True, comment='foreign key')
    title = db.Column(db.String(128), nullable=False, comment=' operation title')
    content = db.Column(db.String(255), nullable=False, comment='operation content')
    status = db.Column(db.Boolean, default=False, comment='operation whether to release')
    isCompleted = db.Column(db.Boolean, default=False, comment='operation whether to be completed')
    teaId = db.Column(db.Integer, db.ForeignKey('teachers.teaId'))






