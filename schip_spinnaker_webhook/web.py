from flask import Flask, url_for, jsonify, request, abort, Blueprint
from werkzeug.exceptions import UnprocessableEntity, HTTPException

from .deployer import deploy
from .status import status
from .models import Deployment

web = Blueprint("web", __name__)


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
    resp = {"code": error.code, "name": error.name, "description": error.description}
    return jsonify(resp), error.code


def create_app():
    app = Flask(__name__)
    app.register_blueprint(web)
    for error_class in HTTPException.__subclasses__():
        if 400 <= error_class.code < 500:
            app.register_error_handler(error_class.code, error_handler)
    return app
