# __init__.py

from flask import Flask
from flask_login import LoginManager
from flask_sqlalchemy import SQLAlchemy
from importlib import import_module
import transformers
import os
from neo4j import GraphDatabase
from langchain_openai import ChatOpenAI
from langchain_huggingface import ChatHuggingFace
from flask_session import Session  # 导入 Flask-Session


db = SQLAlchemy()
login_manager = LoginManager()
sess = Session()

def register_extensions(app):
    db.init_app(app)
    login_manager.init_app(app)
    sess.init_app(app)
    app.config['SECRET_KEY'] = 'your-secret-key'
    

def register_blueprints(app):
    for module_name in ('authentication', 'chat', 'table', 'home'):
        module = import_module('apps.{}.routes'.format(module_name))
        app.register_blueprint(module.blueprint)

def configure_database(app):
    @app.before_request
    def initialize_database():
        try:
            db.create_all()
        except Exception as e:
            print('> Error: DBMS Exception: ' + str(e) )
            # fallback to SQLite
            basedir = os.path.abspath(os.path.dirname(__file__))
            app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + os.path.join(basedir, 'db.sqlite3')
            print('> Fallback to SQLite ')
            db.create_all()

    @app.teardown_request
    def shutdown_session(exception=None):
        db.session.remove()

def initialize_model(app):
    model_id = app.config['MODEL_ID']
    if "llama" in model_id:
        app.config['MODEL_PIPELINE'] = ChatHuggingFace(
            "text-generation",
            model=model_id,
            tokenizer=model_id,
            device=0  # 如果没有GPU，设置为-1
        )
        app.config['MODEL_SOLUTION'] = ChatHuggingFace(
            "text-generation",
            model=model_id,
            tokenizer=model_id,
            device=2  # 如果没有GPU，设置为-1
        )
        app.config['MODEL_PURE'] = ChatHuggingFace(
            "text-generation",
            model=model_id,
            tokenizer=model_id,
            device=1  # 如果没有GPU，设置为-1
        )
        app.config['MODEL_VISUAL'] = ChatHuggingFace(
            "text-generation",
            model=model_id,
            tokenizer=model_id,
            device=1  # 如果没有GPU，设置为-1
        )
    elif "gpt" in model_id:
        api_key = app.config['OPENAI_API_KEY']
        # api_key = os.environ.get('OPENAI_API_KEY')
        app.config['MODEL_PIPELINE'] = ChatOpenAI(api_key=api_key, model="gpt-4o-mini")
        app.config['MODEL_SOLUTION'] = ChatOpenAI(api_key=api_key, model="gpt-4o-mini")
        app.config['MODEL_PURE'] = ChatOpenAI(api_key=api_key, model="gpt-4o-mini")
        app.config['MODEL_VISUAL'] = ChatOpenAI(api_key=api_key, model="gpt-4o-mini")

def initialize_neo4j(app):
    # uri = "bolt://localhost:7687"  # 根据需要替换为您的实际地址
    username = "neo4j"
    password = "neo4j/pwd"
    # app.config['NEO4J_DRIVER'] = GraphDatabase.driver(uri, auth=(username, password))
    print(app.config.get('CURRENT_DATABASE', 'default'))
    print(app.config["DATABASES_URI"])
    uri = app.config["DATABASES_URI"][app.config.get('CURRENT_DATABASE', 'default')]
    app.config['NEO4J_DRIVER'] = GraphDatabase.driver(uri, auth=(username, password))

def create_app(config):
    app = Flask(__name__)
    app.config.from_object(config)
    app.config['SESSION_TYPE'] = 'filesystem'  # 使用文件系统存储 Session
    app.config['SESSION_PERMANENT'] = False    # 可选：设置 session 不永久存储

    register_extensions(app)
    register_blueprints(app)
    configure_database(app)
    initialize_model(app)
    initialize_neo4j(app)
    return app
