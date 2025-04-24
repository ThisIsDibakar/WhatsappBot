from flask import Flask
from flask_cors import CORS

from .routes import customerBp
from .webhook import webhookBp


def create_app():
    app = Flask(__name__)
    CORS(app)

    app.register_blueprint(customerBp)
    app.register_blueprint(webhookBp)

    return app
