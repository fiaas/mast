
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

import pytest

from fiaas_mast.config import Config


class TestConfig(object):
    def test_config_is_read_from_env(self, monkeypatch):
        token = "token"
        certificate = "/path/to/the/ca.crt"
        username = "artifactory_username"
        password = "artifactory_password"
        origin = "https://artifactory.example.com"
        monkeypatch.setenv("APISERVER_TOKEN", token)
        monkeypatch.setenv("APISERVER_CA_CERT", certificate)
        monkeypatch.setenv("ARTIFACTORY_USER", username)
        monkeypatch.setenv("ARTIFACTORY_PWD", password)
        monkeypatch.setenv("ARTIFACTORY_ORIGIN", origin)

        config = Config()
        assert config.APISERVER_TOKEN == token
        assert config.APISERVER_CA_CERT == certificate
        assert config.ARTIFACTORY_USER == username
        assert config.ARTIFACTORY_PWD == password
        assert config.ARTIFACTORY_ORIGIN == origin

    def test_artifactory_credentials_are_missing(self, monkeypatch):
        monkeypatch.setenv("APISERVER_TOKEN", "token")
        monkeypatch.setenv("APISERVER_CA_CERT", "/path/to/the/ca.crt")
        with pytest.raises(RuntimeError):
            config = Config()
            config.ARTIFACTORY_PWD
