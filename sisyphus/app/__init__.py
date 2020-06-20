import logging
import os

from flask import Flask
from flask.logging import default_handler

from .repos_app import repos_hook
from .settings import load_config


def create_app():
    settings = load_config()

    # TODO: get root path as a parameter.
    app = Flask(__name__, root_path=os.getcwd())

    # TODO: configure root logger.
    app.logger.setLevel(logging.INFO)

    logger = logging.getLogger("flask_githubapp")
    logger.addHandler(default_handler)

    # Configure and initialize extensions.
    repos_app = settings.repos_app
    app.config.from_mapping(repos_app.flask_config())
    repos_hook.init_app(app)

    return app
