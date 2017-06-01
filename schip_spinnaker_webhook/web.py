import os
from flask import Flask, url_for, jsonify, request, abort, Blueprint
from werkzeug.exceptions import UnprocessableEntity, HTTPException, InternalServerError

from k8s.client import Client
from .deployer import Deployer
from .models import Release
from .status import status

web = Blueprint("web", __name__)


@web.route("/health", methods=["GET"])
def health_check():
    return jsonify("ok"), 200


@web.route("/deploy/", methods=["PUT", "POST"])
def deploy_handler():
    data = request.get_json(force=True)
    errors = ["Missing key {!r} in input".format(key) for key in ("image", "config_url") if key not in data]
    if errors:
        abort(UnprocessableEntity.code, errors)
    deployer = Deployer(Client())
    application = deployer.deploy(
        Release(data["image"], data["config_url"])
    )
    return jsonify(status(application)), 201, {"Location": url_for("web.status_handler", application=application)}


@web.route("/status/<application>/", methods=["GET"])
def status_handler(application):
    return jsonify(status(application))


def error_handler(error):
    """Render errors as JSON"""
    if not all(hasattr(error, attr) for attr in ("code", "name", "description")):
        error = InternalServerError()
    resp = {
        "code": error.code,
        "name": error.name,
        "description": error.description
    }
    return jsonify(resp), resp["code"]


def assert_namespace_is_set():
    """Namespace where TPRs are created. The namespace where this webhook is running will be used unless an Environment
    variable is passed"""
    if "NAMESPACE" not in os.environ:
        try:
            with open("/var/run/secrets/kubernetes.io/serviceaccount/namespace") as f:
                os.environ["NAMESPACE"] = f.read()
        except OSError:
            raise OSError(
                'The \'NAMESPACE\' environment variable is not set, and the file '
                '\'/var/run/secrets/kubernetes.io/serviceaccount/namespace\' can\'t be read')


def create_app():
    assert_namespace_is_set()
    app = Flask(__name__)
    app.register_blueprint(web)
    for error_class in HTTPException.__subclasses__():
        if 400 <= error_class.code < 600:
            app.register_error_handler(error_class.code, error_handler)
    return app
