"""Probot-compatible configuration for flask-githubapp.

If Probot variables are set, you can use this file with:

    app.config.from_pyfile("probot._config.py")
"""

# TODO: get rid of this file.

import os


GITHUBAPP_ID = os.environ["APP_ID"]
GITHUBAPP_ROUTE = "/hooks/repos"
GITHUBAPP_SECRET = os.environ["WEBHOOK_SECRET"]
GITHUBAPP_KEY = open(os.environ["PRIVATE_KEY_PATH"], "rb").read()
