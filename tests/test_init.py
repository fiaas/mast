import mock

import pytest

from k8s import config as k8s_config
from schip_spinnaker_webhook import configure_k8s_client


def test_k8s_config_from_environment(monkeypatch):
    apiserver_token = "thetoken"
    apiserver_ca_cert = "/path/to/the/ca.crt"
    monkeypatch.setenv("APISERVER_TOKEN", apiserver_token)
    monkeypatch.setenv("APISERVER_CA_CERT", apiserver_ca_cert)

    configure_k8s_client()

    assert k8s_config.api_token == apiserver_token
    assert k8s_config.verify_ssl == apiserver_ca_cert


def test_k8s_config_from_file(monkeypatch):
    apiserver_token = "thetoken"

    with mock.patch("builtins.open", mock.mock_open(read_data=apiserver_token)), mock.patch("os.path.exists") as exists:
        exists.return_value = True
        configure_k8s_client()

    assert k8s_config.api_token == apiserver_token
    assert k8s_config.verify_ssl == "/var/run/secrets/kubernetes.io/serviceaccount/ca.crt"


def test_k8s_config_apiserver_token_missing(monkeypatch):
    monkeypatch.setenv("APISERVER_CA_CERT", "/path/to/the/ca.crt")

    with pytest.raises(RuntimeError):
        configure_k8s_client()


def test_k8s_config_apiserver_ca_cert_missing(monkeypatch):
    monkeypatch.setenv("APISERVER_TOKEN", "thetoken")

    with pytest.raises(RuntimeError):
        configure_k8s_client()
