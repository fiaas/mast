from flask import Flask, url_for, jsonify, request, abort, Blueprint
from werkzeug.exceptions import UnprocessableEntity, HTTPException, InternalServerError

from .deployer import deploy
from .models import Deployment
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
    deployment = Deployment(data["image"], data["config_url"])
    application = deploy(deployment)
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


def create_app():
    app = Flask(__name__)
    app.register_blueprint(web)
    for error_class in HTTPException.__subclasses__():
        if 400 <= error_class.code < 600:
            app.register_error_handler(error_class.code, error_handler)
    return app
