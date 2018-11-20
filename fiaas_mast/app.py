import logging
import sys

from flask import Flask, jsonify
from flask_bootstrap import Bootstrap
from flask_talisman import Talisman, DENY
from k8s import config as k8s_config
from werkzeug.exceptions import InternalServerError, HTTPException

from fiaas_mast.config import Config
from fiaas_mast.web import web

LOGGER = logging.getLogger(__name__)


def create_app(config=None):
    """ Create a Flask app. """
    app = Flask(__name__)

    configure_app(app, config)
    configure_blueprints(app)
    configure_error_handler(app)
    configure_k8s_client(app)
    configure_bootstrap(app)
    configure_logging()

    csp = {'default-src': ["'self'", 'cdnjs.cloudflare.com'],
           'script-src': "'self'",
           'style-src': "'self'",
           'object-src': "'none'"}
    Talisman(app, frame_options=DENY, content_security_policy=csp)
    return app


def configure_bootstrap(app):
    Bootstrap(app)


def configure_app(app, config):
    if config is None:
        config = vars(Config())

    app.config.update(config)


def configure_blueprints(app):
    app.register_blueprint(web)


def configure_error_handler(app):
    app.register_error_handler(Exception, error_handler)
    for error_class in HTTPException.__subclasses__():
        if 400 <= error_class.code < 600:
            app.register_error_handler(error_class.code, error_handler)


def configure_logging():
    root = logging.getLogger()
    root.setLevel(logging.DEBUG)
    stdout_handler = logging.StreamHandler(sys.stdout)
    root.addHandler(stdout_handler)


def configure_k8s_client(app):
    k8s_config.debug = True
    k8s_config.api_token = app.config.get('APISERVER_TOKEN')
    k8s_config.verify_ssl = app.config.get('APISERVER_CA_CERT')


def error_handler(error):
    """Render errors as JSON"""
    if not all(hasattr(error, attr) for attr in ("code", "name", "description")):
        LOGGER.exception("An error occured: %r", error)
        error = InternalServerError()
    resp = {
        "code": error.code,
        "name": error.name,
        "description": error.description
    }
    return jsonify(resp), resp["code"]
