import requests
from flask import current_app as app
from flask import url_for, jsonify, request, abort, Blueprint
from werkzeug.exceptions import UnprocessableEntity

from .deployer import Deployer
from .generator import Generator
from .models import Release
from .status import status
from .common import make_safe_name

web = Blueprint("web", __name__)


@web.route("/health", methods=["GET"])
def health_check():
    return jsonify("ok"), 200


@web.route("/deploy/", methods=["PUT", "POST"])
def deploy_handler():
    data = request.get_json(force=True)
    required_fields = ("application_name", "config_url", "image", "namespace")
    errors = ["Missing key {!r} in input".format(key) for key in required_fields if key not in data]
    if errors:
        abort(UnprocessableEntity.code, errors)
    deployer = Deployer(get_http_client())
    namespace, application_name, deployment_id = deployer.deploy(
        data["namespace"],
        Release(
            data["image"],
            data["config_url"],
            make_safe_name(data["application_name"]),
            data["application_name"],
            data.get("spinnaker_tags", {}),
            data.get("raw_tags", {}))
    )
    response = status(namespace, application_name, deployment_id)
    return jsonify(response._asdict()), 201, {
        "Location": url_for("web.status_handler", _external=True, _scheme="https", namespace=namespace,
                            application=application_name,
                            deployment_id=deployment_id)}


@web.route("/status/<namespace>/<application>/<deployment_id>/", methods=["GET"])
def status_handler(namespace, application, deployment_id):
    response = status(namespace, application, deployment_id)
    return jsonify(response._asdict())


@web.route("/generate/paasbeta_application", methods=["POST"])
def generate_paasbeta_application():
    data = request.get_json(force=True)
    required_fields = ("application_name", "config_url", "image")
    errors = ["Missing key {!r} in input".format(key) for key in required_fields if key not in data]
    if errors:
        abort(UnprocessableEntity.code, errors)
    generator = Generator(get_http_client())
    deployment_id, paasbeta_application = generator.generate_paasbeta_application(
        data["namespace"],
        Release(
            data["image"],
            data["config_url"],
            make_safe_name(data["application_name"]),
            data["application_name"],
            data.get("spinnaker_tags", {}),
            data.get("raw_tags", {}))
    )
    return_body = {
            "manifest": paasbeta_application,
            "deployment_id": deployment_id,
            "status_url": url_for("web.status_handler",
                                  _external=True,
                                  _scheme="https",
                                  namespace=data["namespace"],
                                  application=make_safe_name(data["application_name"]),
                                  deployment_id=deployment_id)
        }
    return jsonify(return_body), 200


def get_http_client():
    http_client = requests.Session()
    http_client.auth = (app.config['ARTIFACTORY_USER'], app.config['ARTIFACTORY_PWD'])

    return http_client
