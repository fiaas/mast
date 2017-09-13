from json import dumps, loads

import pytest

from k8s import config
from fiaas_mast.app import create_app

DEFAULT_CONFIG = {
    'PORT': 5000,
    'DEBUG': True,
    'APISERVER_TOKEN': "default-token",
    'APISERVER_CA_CERT': "/path/to/default.crt",
    'ARTIFACTORY_USER': "default_username",
    'ARTIFACTORY_PWD': "default_password",
}


class TestApp(object):
    def test_k8s_client_is_configured(self):
        token = "token"
        cert = "/path/to/cert.crt"
        DEFAULT_CONFIG['APISERVER_TOKEN'] = token
        DEFAULT_CONFIG['APISERVER_CA_CERT'] = cert
        create_app(DEFAULT_CONFIG)

        assert config.api_token == token
        assert config.verify_ssl == cert

    @pytest.mark.parametrize("action,code", (
            (lambda c: c.get("/"), 404),
            (lambda c: c.get("/deploy/"), 405),
            (lambda c: c.post("/deploy/"), 400),
            (lambda c: c.post("/deploy/", data="{}", content_type="application/json"), 422),
            (lambda c: c.post("/deploy/", data=dumps({"image": "test_image"}), content_type="application/json"), 422),
            (
                    lambda c: c.post("/deploy/", data=dumps({"config_url": "test_url"}),
                                     content_type="application/json"), 422),
    ))
    def test_error_handler(self, action, code):
        app = create_app(DEFAULT_CONFIG)
        resp = action(app.test_client())
        assert resp.status_code == code
        body = loads(resp.data.decode(resp.charset))
        assert body["code"] == code
        assert all(x in body.keys() for x in ("name", "description"))

    def test_app_uses_config_object(self, monkeypatch):
        token = 'token'
        monkeypatch.setenv('APISERVER_TOKEN', token)
        monkeypatch.setenv('APISERVER_CA_CERT', "/path/to/cert.crt")
        monkeypatch.setenv('ARTIFACTORY_USER', "default_username")
        monkeypatch.setenv('ARTIFACTORY_PWD', "default_password")
        app = create_app()
        assert app.config['APISERVER_TOKEN'] == token
