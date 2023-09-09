from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from os import path
from os import environ
from flask_login import LoginManager

db = SQLAlchemy()#database object
DB_NAME = 'database.db'
def create_app():
    USERNAME = environ.get('usr')
    PASSWORD = environ.get('pass')
    IP_ADDR = environ.get('db_ip')
    DB_NAME = environ.get('db_name')
    app = Flask(__name__)
    app.config['SECRET_KEY'] = 'hjshjhdjah kjshkjdhjs'
    app.config["SQLALCHEMY_DATABASE_URI"] = f'postgresql://{USERNAME}:{PASSWORD}@{IP_ADDR}/{DB_NAME}'
    print(app.config["SQLALCHEMY_DATABASE_URI"])
    # app.config["SQLALCHEMY_DATABASE_URI"] = f'postgresql://postgres:5204@localhost/{DB_NAME}'
    # print(app.config["SQLALCHEMY_DATABASE_URI"])
    db.init_app(app)#we are giving our flask app to our database
    
    from .auth import auth_blueprint
    from .views import view_blueprint
    app.register_blueprint(view_blueprint,url_prefix="/")
    app.register_blueprint(auth_blueprint,url_prefix="/")
    
    from .models import User ,original_sentence, Annotated, CurrentProgress
    # with app.app_context():
    #     if not path.exists('annotater/' + DB_NAME):
    #         db.create_all()
    #         print("Created Database!")
            
    login_manager = LoginManager()
    login_manager.login_view = 'auth.login'
    login_manager.init_app(app)
    @login_manager.user_loader
    def load_user(id):
        # print(id)
        return User.query.get(int(id))
    
    return app