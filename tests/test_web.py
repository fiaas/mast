from json import loads, dumps

import mock
import pytest

from schip_spinnaker_webhook.app import create_app
from schip_spinnaker_webhook.deployer import Deployer
from schip_spinnaker_webhook.models import Release

VALID_DEPLOY_DATA = dumps({"image": "test_image", "config_url": "http://example.com", "application_name": "example"})
INVALID_DEPLOY_DATA = dumps({"definitely_not_image": "test_image", "something_other_than_url": "http://example.com"})

DEFAULT_CONFIG = {
    'PORT': 5000,
    'DEBUG': True,
    'NAMESPACE': "default-namespace",
    'APISERVER_TOKEN': "default-token",
    'APISERVER_CA_CERT': "/path/to/default.crt",
    'ARTIFACTORY_USER': "default_username",
    'ARTIFACTORY_PWD': "default_password",
}


@pytest.fixture(autouse=True)
def status():
    with mock.patch("schip_spinnaker_webhook.web.status") as mock_status:
        mock_status.return_value = {"status": "status", "info": "info"}
        yield mock_status


@pytest.fixture
def client():
    app = create_app(DEFAULT_CONFIG)
    with app.app_context():
        with app.test_client() as client:
            yield client


def test_500_error(client):
    with mock.patch.object(Deployer, 'deploy', side_effect=Exception):
        resp = client.post("/deploy/", data=VALID_DEPLOY_DATA, content_type="application/json")
        assert resp.status_code == 500
        body = loads(resp.data.decode(resp.charset))
        assert body["code"] == 500
        assert all(x in body.keys() for x in ("name", "description"))


def test_bad_request_from_client(client):
    with mock.patch.object(Deployer, 'deploy', return_value=("name", "id")):
        resp = client.post("/deploy/", data=INVALID_DEPLOY_DATA, content_type="application/json")
        assert resp.status_code == 422


def test_deploy(client, status):
    with mock.patch.object(Deployer, 'deploy', return_value=("name", "id")) as deploy:
        resp = client.post("/deploy/", data=VALID_DEPLOY_DATA, content_type="application/json")
        assert resp.status_code == 201
        body = loads(resp.data.decode(resp.charset))
        assert all(x in body.keys() for x in ("status", "info"))

        deploy.assert_called_with(DEFAULT_CONFIG.get('NAMESPACE'),
                                  Release("test_image", "http://example.com", "example"))
        status.assert_called_with("name", "id")


def test_status(client, status):
    resp = client.get("/status/test_application/test_id/")
    assert resp.status_code == 200
    body = loads(resp.data.decode(resp.charset))
    assert all(x in body.keys() for x in ("status", "info"))
    status.assert_called_with("test_application", "test_id")


def test_health(client):
    resp = client.get("/health")
    assert resp.status_code == 200
