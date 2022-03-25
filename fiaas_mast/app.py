
# Copyright 2017-2019 The FIAAS Authors
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

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
           'script-src': ["'self'", 'cdnjs.cloudflare.com'],
           'style-src': ["'self'", 'cdnjs.cloudflare.com'],
           'font-src': ["'self'", 'cdnjs.cloudflare.com', 'data:'],
           'object-src': "'none'"}
    Talisman(app, frame_options=DENY, content_security_policy=csp)
    return app


def configure_bootstrap(app):
    Bootstrap(app)


def configure_app(app, config):
    if config is None:
        config = vars(Config())
    app.config['JSON_AS_ASCII'] = False

    app.config.update(config)


def configure_blueprints(app):
    app.register_blueprint(web)


def configure_error_handler(app):
    app.register_error_handler(Exception, error_handler)
    for error_class in HTTPException.__subclasses__():
        if error_class.code is not None and 400 <= error_class.code < 600:
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
