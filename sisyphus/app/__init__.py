import logging
import os

from flask import Flask
from flask.logging import default_handler

from .repos_app import repos_hook


def create_app():
    # TODO: get root path as a parameter.
    app = Flask(__name__, root_path=os.getcwd())

    # TODO: configure root logger.
    app.logger.setLevel(logging.INFO)

    logger = logging.getLogger("flask_githubapp")
    logger.addHandler(default_handler)

    # TODO: read config from YAML file and environment.
    app.config.from_pyfile("probot_config.py")

    # Initialize extensions.
    repos_hook.init_app(app)

    return app
