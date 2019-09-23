
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

import requests
from flask import current_app as app
from flask import url_for, jsonify, request, abort, Blueprint, make_response, render_template
from prometheus_client import generate_latest, CONTENT_TYPE_LATEST, Histogram
from werkzeug.exceptions import UnprocessableEntity

from .application_generator import ApplicationGenerator
from .common import make_safe_name
from .configmap_generator import ConfigMapGenerator
from .deployer import Deployer
from .models import ApplicationConfiguration
from .models import Release
from .status import status

web = Blueprint("web", __name__)

request_histogram = Histogram("web_request_latency", "Request latency in seconds", ["page"])
status_histogram = request_histogram.labels("status")
generate_application_histogram = request_histogram.labels("generate_paasbetaapplication")
generate_configmap_histogram = request_histogram.labels("generate_configmap")
deploy_histogram = request_histogram.labels("deploy")
metrics_histogram = request_histogram.labels("metrics")
health_histogram = request_histogram.labels("health")

BOOTSTRAP_STATUS = dict(UNKNOWN="warning",
                        SUCCESS="success",
                        RUNNING="info",
                        FAILED="danger")


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
            data.get("raw_tags", {}),
            data.get("metadata_annotations", {}))
    )
    response = status(namespace, application_name, deployment_id)
    return jsonify(response._asdict()), 201, {
        "Location": url_for("web.status_handler", _external=True, _scheme=_get_scheme(), namespace=namespace,
                            application=application_name,
                            deployment_id=deployment_id)}


@web.route("/status/<namespace>/<application>/<deployment_id>/", methods=["GET"])
@status_histogram.time()
def status_handler(namespace, application, deployment_id):
    status_object = status(namespace, application, deployment_id)
    status_url = url_for('web.status_view',
                         _external=True,
                         _scheme=_get_scheme(),
                         namespace=namespace,
                         application=application,
                         deployment_id=deployment_id)
    response = {"status": status_object.status,
                "info": "For additional deployment information go to: {}".format(status_url),
                "deployment_status_url": status_url}
    return jsonify(response)


@web.route("/generate/paasbeta_application", methods=["POST"])
@web.route("/generate/application", methods=["POST"])
@generate_application_histogram.time()
def generate_application():
    data = request.get_json(force=True)
    required_fields = ("application_name", "config_url", "image")
    errors = ["Missing key {!r} in input".format(key) for key in required_fields if key not in data]
    if errors:
        abort(UnprocessableEntity.code, errors)
    generator = ApplicationGenerator(get_http_client())
    deployment_id, application = generator.generate_application(
        data["namespace"],
        Release(
            data["image"],
            data["config_url"],
            make_safe_name(data["application_name"]),
            data["application_name"],
            data.get("spinnaker_tags", {}),
            data.get("raw_tags", {}),
            data.get("metadata_annotations", {}))
    )
    return_body = {
        "manifest": application.as_dict(),
        "deployment_id": deployment_id,
        "status_url": url_for("web.status_handler",
                              _external=True,
                              _scheme=_get_scheme(),
                              namespace=data["namespace"],
                              application=make_safe_name(data["application_name"]),
                              deployment_id=deployment_id)
    }
    return jsonify(return_body), 200


@web.route("/generate/configmap", methods=["POST"])
@generate_configmap_histogram.time()
def generate_configmap_application():
    data = request.get_json(force=True)
    required_fields = ("application_name", "application_data_url")
    errors = ["Missing key {!r} in input".format(key) for key in required_fields if key not in data]
    if errors:
        abort(UnprocessableEntity.code, errors)
    generator = ConfigMapGenerator(get_http_client())

    deployment_id, config_map = generator.generate_configmap(
        data["namespace"],
        ApplicationConfiguration(
            data["application_data_url"],
            make_safe_name(data["application_name"]),
            data["application_name"],
            data.get("spinnaker_tags", {}),
            data.get("raw_tags", {}),
            data.get("metadata_annotations", {}))
    )
    return_body = {
        "manifest": config_map,
        "deployment_id": deployment_id
    }
    return jsonify(return_body), 200


@web.route("/_/metrics")
@metrics_histogram.time()
def metrics():
    resp = make_response(generate_latest())
    resp.mimetype = CONTENT_TYPE_LATEST
    return resp


@web.route("/status/view/<namespace>/<application>/<deployment_id>/", methods=["GET"])
@status_histogram.time()
def status_view(namespace, application, deployment_id):
    status_object = status(namespace, application, deployment_id)
    return render_template('statuspage.html',
                           status_object=status_object,
                           namespace=namespace,
                           application=application,
                           deployment_id=deployment_id)


@web.app_template_filter('status_bootstrap')
def status_bootstrap_filter(statuz):
    return BOOTSTRAP_STATUS[statuz] if statuz in BOOTSTRAP_STATUS else BOOTSTRAP_STATUS["UNKNOWN"]


def get_http_client():
    http_client = requests.Session()
    http_client.auth = (app.config['ARTIFACTORY_USER'], app.config['ARTIFACTORY_PWD'])

    return http_client


def _get_scheme():
    return app.config.get('scheme', 'https')
