import mock
import pytest
from json import loads, dumps

from schip_spinnaker_webhook.web import create_app, Deployment

VALID_DEPLOY_DATA = dumps({"image": "test_image", "config_url": "test_url"})
KEEP_MARKER = object()
NOT_SERIALIZABLE = object()


@pytest.fixture(autouse=True)
def deploy():
    with mock.patch("schip_spinnaker_webhook.web.deploy") as mock_deploy:
        mock_deploy.return_value = "test_application"
        yield mock_deploy


@pytest.fixture(autouse=True)
def status():
    with mock.patch("schip_spinnaker_webhook.web.status") as mock_status:
        mock_status.return_value = {"status": "status", "info": "info"}
        yield mock_status


@pytest.fixture
def client():
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


@pytest.mark.parametrize("deploy_value,status_value", (
        (None, KEEP_MARKER),
        (KEEP_MARKER, NOT_SERIALIZABLE)
))
def test_500_error(client, deploy, status, deploy_value, status_value):
    if deploy_value is not KEEP_MARKER:
        deploy.return_value = deploy_value
    if status_value is not KEEP_MARKER:
        status.return_value = status_value
    resp = client.post("/deploy/", data=VALID_DEPLOY_DATA, content_type="application/json")
    assert resp.status_code == 500
    body = loads(resp.data.decode(resp.charset))
    assert body["code"] == 500
    assert all(x in body.keys() for x in ("name", "description"))


def test_deploy(client, deploy, status):
    resp = client.post("/deploy/", data=VALID_DEPLOY_DATA, content_type="application/json")
    assert resp.status_code == 201
    body = loads(resp.data.decode(resp.charset))
    assert all(x in body.keys() for x in ("status", "info"))
    assert not any(x in body.keys() for x in ("name", "description", "code"))
    deploy.assert_called_with(Deployment("test_image", "test_url"))
    status.assert_called_with("test_application")


def test_status(client, status):
    resp = client.get("/status/test_application/")
    assert resp.status_code == 200
    body = loads(resp.data.decode(resp.charset))
    assert all(x in body.keys() for x in ("status", "info"))
    status.assert_called_with("test_application")
