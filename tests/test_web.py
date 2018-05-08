from json import loads, dumps
from urllib.parse import urlparse

import mock
import pytest

from fiaas_mast.app import create_app
from fiaas_mast.deployer import Deployer
from fiaas_mast.generator import Generator
from fiaas_mast.models import Release, Status

DEFAULT_NAMESPACE = "default-namespace"

VALID_DEPLOY_DATA = {
    "image": "test_image",
    "config_url": "http://example.com",
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
}

SPINNAKER_TAGS = {}


@pytest.fixture(autouse=True)
def status():
    with mock.patch("fiaas_mast.web.status") as mock_status:
        mock_status.return_value = Status(status="status", info="info")
        yield mock_status


@pytest.fixture(autouse=True)
def select_models():
    with mock.patch('fiaas_mast.deployer.select_models') as m:
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


def test_deploy_config_url_missing_schema(client, status):
    deploy_data = VALID_DEPLOY_DATA.copy()
    deploy_data.update({"config_url": "missing_schema"})
    resp = client.post("/deploy/", data=dumps(deploy_data), content_type="application/json")
    assert resp.status_code == 422
    response_json = loads(resp.get_data())
    assert response_json == {"code": 422, "name": "Unprocessable Entity", "description": "Invalid config_url"}


def test_deploy_config_url_missing_host(client, status):
    deploy_data = VALID_DEPLOY_DATA.copy()
    deploy_data.update({"config_url": "http://"})
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
                                  Release("test_image", "http://example.com", "example", "example", SPINNAKER_TAGS))
        status.assert_called_with("some-namespace", "app-name", "deploy_id")


def test_generate_paasbeta_application(client, status):
    with mock.patch.object(Generator, 'generate_paasbeta_application', return_value=("deployment_id", {
        "foo": "bar"
    })) as generate_paasbeta_application:
        resp = client.post("/generate/paasbeta_application", data=dumps(VALID_DEPLOY_DATA),
                           content_type="application/json")
        assert resp.status_code == 200
        body = loads(resp.data.decode(resp.charset))
        assert urlparse(body["status_url"]).path == "/status/default-namespace/example/deployment_id/"
        generate_paasbeta_application.assert_called_with(
            DEFAULT_NAMESPACE, Release("test_image", "http://example.com", "example", "example", SPINNAKER_TAGS)
        )


def test_generate_paasbeta_application_invalid_data(client, status):
    resp = client.post("/generate/paasbeta_application", data=dumps(INVALID_DEPLOY_DATA),
                       content_type="application/json")
    assert resp.status_code == 422


def test_generate_paasbeta_application_config_url_missing_schema(client, status):
    deploy_data = VALID_DEPLOY_DATA.copy()
    deploy_data.update({"config_url": "missing_schema"})
    resp = client.post("/generate/paasbeta_application", data=dumps(deploy_data), content_type="application/json")
    assert resp.status_code == 422
    response_json = loads(resp.get_data())
    assert response_json == {"code": 422, "name": "Unprocessable Entity", "description": "Invalid config_url"}


def test_generate_paasbeta_application_config_url_missing_host(client, status):
    deploy_data = VALID_DEPLOY_DATA.copy()
    deploy_data.update({"config_url": "http://"})
    resp = client.post("/generate/paasbeta_application", data=dumps(deploy_data), content_type="application/json")
    assert resp.status_code == 422
    response_json = loads(resp.get_data())
    assert response_json == {"code": 422, "name": "Unprocessable Entity", "description": "Invalid config_url"}


def test_status(client, status):
    resp = client.get("/status/test_namespace/test_application/test_id/")
    assert resp.status_code == 200
    body = loads(resp.data.decode(resp.charset))
    assert all(x in body.keys() for x in ("status", "info"))
    status.assert_called_with("test_namespace", "test_application", "test_id")


def test_health(client):
    resp = client.get("/health")
    assert resp.status_code == 200
