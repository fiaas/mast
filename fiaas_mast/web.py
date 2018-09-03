import requests
from flask import current_app as app
from flask import url_for, jsonify, request, abort, Blueprint, make_response
from prometheus_client import generate_latest, CONTENT_TYPE_LATEST, Histogram
from werkzeug.exceptions import UnprocessableEntity

from .deployer import Deployer
from .generator import Generator
from .models import Release
from .status import status
from .common import make_safe_name

web = Blueprint("web", __name__)

request_histogram = Histogram("web_request_latency", "Request latency in seconds", ["page"])
status_histogram = request_histogram.labels("status")
generate_paasbetaapplication_histogram = request_histogram.labels("generate_paasbetaapplication")
deploy_histogram = request_histogram.labels("deploy")
metrics_histogram = request_histogram.labels("metrics")
health_histogram = request_histogram.labels("health")


@web.route("/health", methods=["GET"])
@health_histogram.time()
def health_check():
    return jsonify("ok"), 200


@web.route("/deploy/", methods=["PUT", "POST"])
@deploy_histogram.time()
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
@status_histogram.time()
def status_handler(namespace, application, deployment_id):
    response = status(namespace, application, deployment_id)
    return jsonify(response._asdict())


@web.route("/generate/paasbeta_application", methods=["POST"])
@generate_paasbetaapplication_histogram.time()
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


@web.route("/_/metrics")
@metrics_histogram.time()
def metrics():
    resp = make_response(generate_latest())
    resp.mimetype = CONTENT_TYPE_LATEST
    return resp


def get_http_client():
    http_client = requests.Session()
    http_client.auth = (app.config['ARTIFACTORY_USER'], app.config['ARTIFACTORY_PWD'])

    return http_client
