import mock
import pytest

from fiaas_mast.config import Config


class TestConfig(object):
    def test_config_is_read_from_env(self, monkeypatch):
        token = "token"
        certificate = "/path/to/the/ca.crt"
        username = "artifactory_username"
        password = "artifactory_password"
        monkeypatch.setenv("APISERVER_TOKEN", token)
        monkeypatch.setenv("APISERVER_CA_CERT", certificate)
        monkeypatch.setenv("ARTIFACTORY_USER", username)
        monkeypatch.setenv("ARTIFACTORY_PWD", password)

        config = Config()
        assert config.APISERVER_TOKEN == token
        assert config.APISERVER_CA_CERT == certificate
        assert config.ARTIFACTORY_USER == username
        assert config.ARTIFACTORY_PWD == password

    def test_k8s_token_is_read_from_file_when_env_is_not_defined(self, monkeypatch):
        token = "token"
        monkeypatch.setenv("APISERVER_CA_CERT", "/path/to/the/ca.crt")
        monkeypatch.setenv("ARTIFACTORY_USER", "username")
        monkeypatch.setenv("ARTIFACTORY_PWD", "password")

        with mock.patch("builtins.open", mock.mock_open(read_data=token)), mock.patch("os.path.exists") as exists:
            exists.return_value = True
            config = Config()
            assert config.APISERVER_TOKEN == token

    def test_k8s_cert_is_read_from_file_when_env_is_not_defined(self, monkeypatch):
        certificate = "/var/run/secrets/kubernetes.io/serviceaccount/ca.crt"
        monkeypatch.setenv("APISERVER_TOKEN", "token")
        monkeypatch.setenv("ARTIFACTORY_USER", "username")
        monkeypatch.setenv("ARTIFACTORY_PWD", "password")

        with mock.patch("os.path.exists") as exists:
            exists.return_value = True
            config = Config()
            assert config.APISERVER_CA_CERT == certificate

    def test_k8s_config_apiserver_token_missing(self, monkeypatch):
        certificate = "/path/to/the/ca.crt"
        monkeypatch.setenv("APISERVER_CA_CERT", certificate)
        monkeypatch.setenv("ARTIFACTORY_USER", "username")
        monkeypatch.setenv("ARTIFACTORY_PWD", "password")

        with pytest.raises(RuntimeError):
            config = Config()
            config.APISERVER_TOKEN

    def test_k8s_config_apiserver_ca_cert_missing(self, monkeypatch):
        monkeypatch.setenv("APISERVER_TOKEN", "thetoken")
        monkeypatch.setenv("ARTIFACTORY_USER", "username")
        monkeypatch.setenv("ARTIFACTORY_PWD", "password")

        with pytest.raises(RuntimeError):
            config = Config()
            config.APISERVER_CA_CERT

    def test_artifactory_credentials_are_missing(self, monkeypatch):
        monkeypatch.setenv("APISERVER_TOKEN", "token")
        monkeypatch.setenv("APISERVER_CA_CERT", "/path/to/the/ca.crt")
        with pytest.raises(RuntimeError):
            config = Config()
            config.ARTIFACTORY_PWD
