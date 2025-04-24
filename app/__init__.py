from flask import Flask
from flask_cors import CORS

from .routes import customerBp


def create_app():
    app = Flask(__name__)
    CORS(app)

    app.register_blueprint(customerBp)

    return app
