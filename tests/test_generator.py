import pytest
from mock import MagicMock

from fiaas_mast.generator import generate_random_uuid_string, Generator
from fiaas_mast.models import Release

APPLICATION_NAME = "test_image"
DEPLOYMENT_ID = "deadbeef-abba-cafe-1337-baaaaaaaaaad"
VALID_IMAGE_NAME = "test_image:a1b2c3d"
VALID_DEPLOY_CONFIG_URL = "http://url_to_config.file"
ANY_NAMESPACE = "any-namespace"

VALID_DEPLOY_CONFIG_V3 = """
version: 3
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

BASE_PAASBETA_APPLICATION = {
    "apiVersion": "schibsted.io/v1beta",
    "kind": "PaasbetaApplication",
    "metadata": {
        "labels": {
            "app": "test_image",
            "fiaas/deployment_id": "deadbeef-abba-cafe-1337-baaaaaaaaaad"
        },
        "name": "test_image",
        "namespace": "target-namespace"
    },
    "spec": {
        "admin_access": True,
        "config": {
            "volume": True
        },
        "healthchecks": {
            "liveness": {
                "http": {
                    "path": "/healthz"
                }
            }
        },
        "image": "test_image:a1b2c3d",
        "ports": [{
            "target_port": 5000
        }],
        "replicas": 1,
        "resources": {
            "requests": {
                "memory": "128m"
            }
        },
        "version": 3
    }
}


class TestGeneratePaasbetaApplication(object):
    @pytest.mark.parametrize(
        "config,target_namespace,expected_namespace", ((VALID_DEPLOY_CONFIG_V3, ANY_NAMESPACE, ANY_NAMESPACE),
                                                       (VALID_DEPLOY_CONFIG_V3, "custom-namespace",
                                                        "custom-namespace"), )
    )
    def test_generator_creates_object_of_given_type(self, config, target_namespace, expected_namespace):
        http_client = _given_config_url_response_content_is(config)
        generator = Generator(http_client, create_deployment_id=lambda: DEPLOYMENT_ID)
        returned_paasbeta_application = generator.generate_paasbeta_application(
            target_namespace=target_namespace,
            release=Release(VALID_IMAGE_NAME, VALID_DEPLOY_CONFIG_URL, APPLICATION_NAME)
        )
        expected_paasbeta_application = BASE_PAASBETA_APPLICATION
        expected_paasbeta_application["metadata"]["namespace"] = expected_namespace
        assert returned_paasbeta_application == expected_paasbeta_application


class TestUUID:
    def test_uuid_generation(self):
        uuid1 = generate_random_uuid_string()
        uuid2 = generate_random_uuid_string()
        assert uuid1 != uuid2


def _given_config_url_response_content_is(config):
    http_client = MagicMock(spec="requests.Session")
    config_response = MagicMock()
    config_response.text = config

    http_client_get = MagicMock()
    http_client_get.return_value = config_response
    http_client.get = http_client_get

    return http_client
