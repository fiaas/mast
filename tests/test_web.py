from json import loads, dumps

import mock
import os
import pytest

from schip_spinnaker_webhook.deployer import Deployer
from schip_spinnaker_webhook.models import Release
from schip_spinnaker_webhook.web import create_app

VALID_DEPLOY_DATA = dumps({"image": "test_image", "config_url": "http://example.com"})
INVALID_DEPLOY_DATA = dumps({"definitely_not_image": "test_image", "something_other_than_url": "http://example.com"})
KEEP_MARKER = object()
NOT_SERIALIZABLE = object()
NAMESPACE_FROM_FILE = 'file-namespace'


@pytest.fixture(autouse=True)
def status():
    with mock.patch("schip_spinnaker_webhook.web.status") as mock_status:
        mock_status.return_value = {"status": "status", "info": "info"}
        yield mock_status


@pytest.fixture
def client():
    os.environ['NAMESPACE'] = 'env-namespace'
    app = create_app()
    with app.app_context():
        with app.test_client() as client:
            yield client


@pytest.mark.parametrize("action,code", (
        (lambda c: c.get("/"), 404),
        (lambda c: c.get("/deploy/"), 405),
        (lambda c: c.post("/deploy/"), 400),
        (lambda c: c.post("/deploy/", data="{}", content_type="application/json"), 422),
        (lambda c: c.post("/deploy/", data=dumps({"image": "test_image"}), content_type="application/json"), 422),
        (lambda c: c.post("/deploy/", data=dumps({"config_url": "test_url"}), content_type="application/json"), 422),
))
def test_error_handler(client, action, code):
    resp = action(client)
    assert resp.status_code == code
    body = loads(resp.data.decode(resp.charset))
    assert body["code"] == code
    assert all(x in body.keys() for x in ("name", "description"))


def test_500_error(client):
    with mock.patch.object(Deployer, 'deploy', side_effect=Exception):
        resp = client.post("/deploy/", data=VALID_DEPLOY_DATA, content_type="application/json")
        assert resp.status_code == 500
        body = loads(resp.data.decode(resp.charset))
        assert body["code"] == 500
        assert all(x in body.keys() for x in ("name", "description"))


def test_bad_request_from_client(client):
    with mock.patch.object(Deployer, 'deploy', return_value=True):
        resp = client.post("/deploy/", data=INVALID_DEPLOY_DATA, content_type="application/json")
        assert resp.status_code == 422


def test_deploy(client, status):
    with mock.patch.object(Deployer, 'deploy', return_value="test_application") as deploy:
        resp = client.post("/deploy/", data=VALID_DEPLOY_DATA, content_type="application/json")
        assert resp.status_code == 201
        body = loads(resp.data.decode(resp.charset))
        assert all(x in body.keys() for x in ("status", "info"))

        deploy.assert_called_with(Release("test_image", "http://example.com"))
        status.assert_called_with("test_application")


def test_status(client, status):
    resp = client.get("/status/test_application/")
    assert resp.status_code == 200
    body = loads(resp.data.decode(resp.charset))
    assert all(x in body.keys() for x in ("status", "info"))
    status.assert_called_with("test_application")


def test_namespace_is_read_from_env_variable():
    os.environ['NAMESPACE'] = 'env-namespace'
    create_app()
    assert os.environ['NAMESPACE'] == 'env-namespace'
    del os.environ['NAMESPACE']


def test_use_file_fallback_for_namespace_when_env_variable_is_not_set():
    with mock.patch('builtins.open', mock.mock_open(read_data=NAMESPACE_FROM_FILE)):
        create_app()
        assert os.environ['NAMESPACE'] == NAMESPACE_FROM_FILE


def test_fail_when_file_fallback_for_namespace_is_not_available_and_env_variable_is_not_set():
    with mock.patch('builtins.open') as mocked_open:
        with pytest.raises(OSError):
            if 'NAMESPACE' in os.environ:
                del os.environ['NAMESPACE']
            mocked_open.side_effect = OSError()
            create_app()
