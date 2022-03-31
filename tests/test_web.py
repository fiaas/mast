
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

from json import loads, dumps
from urllib.parse import urlparse

import mock
import pytest

from fiaas_mast.app import create_app
from fiaas_mast.application_generator import ApplicationGenerator
from fiaas_mast.configmap_generator import ConfigMapGenerator
from fiaas_mast.deployer import Deployer
from fiaas_mast.fiaas import FiaasApplication
from fiaas_mast.models import Release, Status, ApplicationConfiguration
from fiaas_mast.web import ArtifactoryAuth, get_http_client
import requests
from requests.models import Request

DEFAULT_NAMESPACE = "default-namespace"

VALID_DEPLOY_DATA = {
    "image": "test_image",
    "config_url": "http://example.com",
    "application_name": "example",
    "namespace": DEFAULT_NAMESPACE
}

VALID_APPLICATIONDATA_REQUEST = {
    "application_data_url": "http://example.com",
    "application_name": "example",
    "namespace": DEFAULT_NAMESPACE
}

INVALID_APPLICATIONDATA_REQUEST = {
    "not_application_data_url": "http://example.com",
    "application_name": "example",
    "namespace": DEFAULT_NAMESPACE
}

INVALID_DEPLOY_DATA = {"definitely_not_image": "test_image", "something_other_than_url": "http://example.com"}

DEFAULT_CONFIG = {
    'PORT': 5000,
    'DEBUG': True,
    'NAMESPACE': DEFAULT_NAMESPACE,
    'APISERVER_TOKEN': "default-token",
    'APISERVER_CA_CERT': "/path/to/default.crt",
    'ARTIFACTORY_USER': "default_username",
    'ARTIFACTORY_PWD': "default_password",
    'ARTIFACTORY_ORIGIN': "https://www.example.com",
}

SPINNAKER_TAGS = {}
RAW_TAGS = {}
RAW_LABELS = {}


@pytest.fixture(autouse=True)
def status():
    with mock.patch("fiaas_mast.web.status") as mock_status:
        mock_status.return_value = Status(status="status", info="info", logs=['logline 1', 'logline 2', 'more logs'])
        yield mock_status


@pytest.fixture(autouse=True)
def check_models_deployer():
    with mock.patch('fiaas_mast.deployer.check_models') as m:
        m.return_value = (None, None)
        yield m


@pytest.fixture(autouse=True)
def check_models_generator():
    with mock.patch('fiaas_mast.application_generator.check_models') as m:
        m.return_value = (None, None)
        yield m


@pytest.fixture
def client():
    app = create_app(DEFAULT_CONFIG)
    with app.app_context():
        with app.test_client() as client:
            yield client


def test_deploy_500_error_on_unhandled_exception(client):
    with mock.patch.object(Deployer, 'deploy', side_effect=Exception):
        resp = client.post("/deploy/", data=dumps(VALID_DEPLOY_DATA), content_type="application/json")
        assert resp.status_code == 500
        body = loads(resp.data.decode(resp.charset))
        assert body["code"] == 500
        assert all(x in body.keys() for x in ("name", "description"))


def test_deploy_bad_request_from_client(client):
    with mock.patch.object(Deployer, 'deploy', return_value=("name", "id")):
        resp = client.post("/deploy/", data=dumps(INVALID_DEPLOY_DATA), content_type="application/json")
        assert resp.status_code == 422


@pytest.mark.parametrize("config_url", (
    "missing_schema",  # should cause MissingSchema
    "http://",  # should cause InvalidURL
))
def test_deploy_invalid_config_url(client, config_url):
    deploy_data = VALID_DEPLOY_DATA.copy()
    deploy_data.update({"config_url": config_url})
    resp = client.post("/deploy/", data=dumps(deploy_data), content_type="application/json")
    assert resp.status_code == 422
    response_json = loads(resp.get_data())
    assert response_json == {"code": 422, "name": "Unprocessable Entity", "description": "Invalid config_url"}


def test_deploy(client, status):
    with mock.patch.object(Deployer, 'deploy', return_value=("some-namespace", "app-name", "deploy_id")) as deploy:
        resp = client.post("/deploy/", data=dumps(VALID_DEPLOY_DATA), content_type="application/json")
        assert resp.status_code == 201
        assert urlparse(resp.location).path == "/status/some-namespace/app-name/deploy_id/"

        body = loads(resp.data.decode(resp.charset))
        assert all(x in body.keys() for x in ("status", "info"))

        deploy.assert_called_with(DEFAULT_NAMESPACE,
                                  Release("test_image", "http://example.com", "example", "example", SPINNAKER_TAGS,
                                          RAW_TAGS, RAW_LABELS, {}))
        status.assert_called_with("some-namespace", "app-name", "deploy_id")


def test_generate_application(client):
    with mock.patch.object(ApplicationGenerator, 'generate_application',
                           return_value=("deployment_id", FiaasApplication())) as generate_application:
        resp = client.post("/generate/application", data=dumps(VALID_DEPLOY_DATA),
                           content_type="application/json")
        assert resp.status_code == 200
        body = loads(resp.data.decode(resp.charset))
        assert urlparse(body["status_url"]).path == "/status/default-namespace/example/deployment_id/"
        generate_application.assert_called_with(
            DEFAULT_NAMESPACE, Release("test_image", "http://example.com", "example", "example", SPINNAKER_TAGS,
                                       RAW_TAGS, RAW_LABELS, {})
        )


def test_generate_paasbeta_application_invalid_data(client):
    resp = client.post("/generate/application", data=dumps(INVALID_DEPLOY_DATA),
                       content_type="application/json")
    assert resp.status_code == 422


@pytest.mark.parametrize("config_url", (
    "missing_schema",  # should cause MissingSchema
    "http://",  # should cause InvalidURL
))
def test_generate_paasbeta_application_invalid_config_url(client, config_url):
    deploy_data = VALID_DEPLOY_DATA.copy()
    deploy_data.update({"config_url": config_url})
    resp = client.post("/generate/application", data=dumps(deploy_data), content_type="application/json")
    assert resp.status_code == 422
    response_json = loads(resp.get_data())
    assert response_json == {"code": 422,
                             "name": "Unprocessable Entity",
                             "description": "Invalid config_url: {}".format(config_url)}


def test_generate_configmap(client):
    with mock.patch.object(ConfigMapGenerator, 'generate_configmap',
                           return_value=("deployment_id", {"foo": "bar", "utf8": "ú"})) as generate_configmap:
        resp = client.post("/generate/configmap", data=dumps(VALID_APPLICATIONDATA_REQUEST),
                           content_type="application/json")
        assert resp.status_code == 200
        assert "ú" in resp.data.decode(resp.charset)

        generate_configmap.assert_called_with(
            DEFAULT_NAMESPACE, ApplicationConfiguration("http://example.com", "example", "example", SPINNAKER_TAGS,
                                                        RAW_TAGS, {})
        )


def test_generate_configmap_invalid_data(client):
    resp = client.post("/generate/configmap", data=dumps(INVALID_APPLICATIONDATA_REQUEST),
                       content_type="application/json")
    assert resp.status_code == 422


def test_status(client, status):
    resp = client.get("/status/test_namespace/test_application/test_id/")
    assert resp.status_code == 200
    body = loads(resp.data.decode(resp.charset))
    assert all(x in body.keys() for x in ("status", "info", "deployment_status_url"))
    status.assert_called_with("test_namespace", "test_application", "test_id")
    assert urlparse(body["deployment_status_url"]).path == "/status/view/test_namespace/test_application/test_id/"


def test_status_view(client, status):
    resp = client.get("/status/view/test_namespace/test_application/test_id/")
    assert resp.status_code == 200
    status.assert_called_with("test_namespace", "test_application", "test_id")


def test_health(client):
    resp = client.get("/health")
    assert resp.status_code == 200


def test_status_bootstrap_filter():
    app = create_app(DEFAULT_CONFIG)
    assert app.jinja_env.filters['status_bootstrap']('not_a_valid_status') == 'warning'
    assert app.jinja_env.filters['status_bootstrap']('UNKNOWN') == 'warning'
    assert app.jinja_env.filters['status_bootstrap']('SUCCESS') == 'success'
    assert app.jinja_env.filters['status_bootstrap']('RUNNING') == 'info'
    assert app.jinja_env.filters['status_bootstrap']('FAILED') == 'danger'


def test_artifactory_auth_for_allowed_origin():
    auth = ArtifactoryAuth("username", "password", "https://artifactory.example.com")
    input_request = Request(url="https://artifactory.example.com/some/path")
    result = auth(input_request)
    assert 'Authorization' in result.headers


@pytest.mark.parametrize("url", ["http://artifactory.example.com", "https://artifactory.example.com"])
def test_http_client_configured_for_retry(url):
    app = create_app(DEFAULT_CONFIG)
    with app.app_context():
        session = get_http_client()
        adapter = session.get_adapter(url)
        assert adapter.max_retries.total > 0
        assert requests.codes.too_many_requests in adapter.max_retries.status_forcelist
        assert requests.codes.ok not in adapter.max_retries.status_forcelist


@pytest.mark.parametrize(
    "url",
    (
        "http://artifactory.example.com/some/path",
        "https://foo.example.com/some/path",
        "https://artifactory.example.com.other.com",
    )
)
def test_artifactory_auth_for_disallowed_origin(url):
    auth = ArtifactoryAuth("username", "password", "https://artifactory.example.com")
    input_request = Request(url=url)
    result = auth(input_request)
    assert 'Authorization' not in result.headers
