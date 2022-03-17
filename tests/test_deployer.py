
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
import yaml
from k8s.models.common import ObjectMeta
from mock import MagicMock, patch

from fiaas_mast.deployer import generate_random_uuid_string, Deployer
from fiaas_mast.fiaas import FiaasApplicationSpec, FiaasApplication
from fiaas_mast.models import Release

APPLICATION_NAME = "test_image"
SPINNAKER_TAGS = {}
RAW_TAGS = {}
RAW_LABELS = {}
DEPLOYMENT_ID = "deadbeef-abba-cafe-1337-baaaaaaaaaad"
VALID_IMAGE_NAME = "test_image:a1b2c3d"
VALID_DEPLOY_CONFIG_URL = "http://url_to_config.file"
ANY_NAMESPACE = "any-namespace"

VALID_DEPLOY_CONFIG = b"""
version: 2
admin_access: true
replicas: 1
resources:
  requests:
    memory: 128m
ports:
  - target_port: 5000
healthchecks:
  liveness:
    http:
      path: /healthz
config:
  volume: true
"""

VALID_DEPLOY_CONFIG_WITH_NAMESPACE = b"""
version: 2
namespace: custom-namespace
admin_access: true
replicas: 1
resources:
  requests:
    memory: 128m
ports:
  - target_port: 5000
healthchecks:
  liveness:
    http:
      path: /healthz
config:
  volume: true
"""

VALID_DEPLOY_CONFIG_WITH_NON_ISO_8859_1_CHARS = b"""
version: 2
namespace: \xc3\x9aj-tal\xc3\xa1latok
admin_access: true
replicas: 1
resources:
  requests:
    memory: 128m
ports:
  - target_port: 5000
healthchecks:
  liveness:
    http:
      path: /healthz
config:
  volume: true
"""

VALID_DEPLOY_CONFIG_WITH_NAMESPACE_V3 = b"""
version: 3
namespace: custom-namespace
admin_access: true
replicas: 1
resources:
  requests:
    memory: 128m
ports:
  - target_port: 5000
healthchecks:
  liveness:
    http:
      path: /healthz
config:
  volume: true
"""

VALID_DEPLOY_CONFIG_WITH_INGRESS_1 = b"""
version: 3
ingress:
  - host: foo.example.com
"""

VALID_DEPLOY_CONFIG_WITH_INGRESS_2 = b"""
version: 3
"""


class TestCreateDeploymentInK8s(object):
    @pytest.fixture
    def object_types(self):
        return FiaasApplication, FiaasApplicationSpec

    @pytest.fixture
    def k8s_model(self, object_types):
        application_model, _ = object_types
        application_instance = application_model()
        application_instance.save = MagicMock()
        return application_instance

    @pytest.fixture
    def get(self, k8s_model):
        with patch('k8s.base.ApiMixIn.get') as m:
            m.return_value = k8s_model
            yield m

    @pytest.fixture
    def get_or_create(self, k8s_model):
        with patch('k8s.base.ApiMixIn.get_or_create') as m:
            m.return_value = k8s_model
            yield m

    @pytest.fixture(autouse=True)
    def check_models(self, object_types):
        with patch('fiaas_mast.deployer.check_models') as m:
            m.return_value = object_types
            yield m

    @pytest.mark.parametrize("config,target_namespace,expected_namespace", (
        (VALID_DEPLOY_CONFIG, ANY_NAMESPACE, ANY_NAMESPACE),
        (VALID_DEPLOY_CONFIG_WITH_NON_ISO_8859_1_CHARS, "Új-találatok", "Új-találatok"),
        (VALID_DEPLOY_CONFIG_WITH_NAMESPACE, ANY_NAMESPACE, "custom-namespace"),
        (VALID_DEPLOY_CONFIG_WITH_NAMESPACE_V3, "target-namespace", "target-namespace"),
    ))
    def test_deployer_creates_object_of_given_type(self,
                                                   get,
                                                   k8s_model,
                                                   object_types,
                                                   config,
                                                   target_namespace,
                                                   expected_namespace):
        http_client = _given_config_url_response_content_is(config)
        _, spec_model = object_types
        deployer = Deployer(http_client, create_deployment_id=lambda: DEPLOYMENT_ID)
        returned_namespace, returned_name, returned_id = deployer.deploy(
            target_namespace=target_namespace,
            release=Release(
                VALID_IMAGE_NAME,
                VALID_DEPLOY_CONFIG_URL,
                APPLICATION_NAME,
                APPLICATION_NAME,
                SPINNAKER_TAGS,
                RAW_TAGS,
                RAW_LABELS,
                ""
            )
        )

        assert returned_namespace == expected_namespace
        assert returned_name == APPLICATION_NAME
        assert returned_id == DEPLOYMENT_ID
        http_client.get.assert_called_once_with(VALID_DEPLOY_CONFIG_URL)

        metadata = ObjectMeta(
            name=APPLICATION_NAME,
            namespace=expected_namespace,
            labels={"fiaas/deployment_id": DEPLOYMENT_ID, "app": APPLICATION_NAME}
        )
        spec = spec_model(
            application=APPLICATION_NAME,
            image=VALID_IMAGE_NAME,
            config=yaml.safe_load(config)
        )
        get.assert_called_once_with(APPLICATION_NAME, expected_namespace)
        assert metadata == k8s_model.metadata
        assert spec == k8s_model.spec
        k8s_model.save.assert_called_once()

    @pytest.mark.usefixtures("get")
    def test_ingress_is_updated(self, k8s_model, object_types):
        _, spec_model = object_types
        existing_spec = spec_model(
            application=APPLICATION_NAME,
            image=VALID_IMAGE_NAME,
            config=yaml.safe_load(VALID_DEPLOY_CONFIG_WITH_INGRESS_1)
        )
        k8s_model.spec = existing_spec
        http_client = _given_config_url_response_content_is(VALID_DEPLOY_CONFIG_WITH_INGRESS_2)
        deployer = Deployer(http_client, create_deployment_id=lambda: DEPLOYMENT_ID)
        deployer.deploy(
            target_namespace="default",
            release=Release(
                VALID_IMAGE_NAME,
                VALID_DEPLOY_CONFIG_URL,
                APPLICATION_NAME,
                APPLICATION_NAME,
                SPINNAKER_TAGS,
                RAW_TAGS,
                RAW_LABELS,
                ""
            )
        )
        expected_spec = spec_model(
            application=APPLICATION_NAME,
            image=VALID_IMAGE_NAME,
            config=yaml.safe_load(VALID_DEPLOY_CONFIG_WITH_INGRESS_2)
        )
        assert k8s_model.spec == expected_spec
        k8s_model.save.assert_called_once()


class TestUUID:
    def test_uuid_generation(self):
        uuid1 = generate_random_uuid_string()
        uuid2 = generate_random_uuid_string()
        assert uuid1 != uuid2


def _given_config_url_response_content_is(config):
    http_client = MagicMock(spec="requests.Session")
    config_response = MagicMock()
    config_response.content = config

    http_client_get = MagicMock()
    http_client_get.return_value = config_response
    http_client.get = http_client_get

    return http_client
