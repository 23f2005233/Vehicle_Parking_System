from flask import Flask, render_template, request
from controllers.database import db
from controllers.create_database_instances import create_tables

def create_app():
    app = Flask(__name__, template_folder='templates')
    app.config.from_object('controllers.config.config')
    db.init_app(app)
    app.app_context().push()
    return app

app = create_app()

from controllers.routes import *
if __name__ == '__main__':
    create_tables()
    app.run(debug=True)