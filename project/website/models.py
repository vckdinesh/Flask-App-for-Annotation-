from . import db
from flask_login import UserMixin
from sqlalchemy.sql import func

class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(150), unique=True, nullable=False)
    role = db.Column(db.String(15))
    password = db.Column(db.String(150))
    
    annotations = db.relationship('Annotated', backref='user', lazy=True)
    current_progress = db.relationship('CurrentProgress', backref='user', uselist=False, lazy=True)

class original_sentence(db.Model):
    sentence_index = db.Column(db.Integer, primary_key=True)
    comments = db.Column(db.String(1000),nullable=False)
    comments_tagged = db.Column(db.String(10000))
    lang_tag = db.Column(db.String(1000))
    annotation_status = db.Column(db.Boolean, default=False, nullable=False)
    no_of_words = db.Column(db.Integer)
    progress=db.Column(db.Integer)
    
    
    annotated_sentence = db.relationship('Annotated', backref='original_sentence', uselist=False, lazy=True)

class Annotated(db.Model,UserMixin):
    annotation_id = db.Column(db.Integer, primary_key=True)
    sent_id = db.Column(db.Integer, db.ForeignKey('original_sentence.sentence_index'))
    pos_tag = db.Column(db.String(1000))
    new_lang_tag = db.Column(db.String(1000))
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))

    current_progress = db.relationship('CurrentProgress', backref='annotated', uselist=False, lazy=True)

class CurrentProgress(db.Model):
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), primary_key=True)
    last_tagged_id = db.Column(db.Integer, db.ForeignKey('annotated.annotation_id'))
    no_of_tagged = db.Column(db.Integer)
    last_status= db.Column(db.Boolean, default=False, nullable=False)
