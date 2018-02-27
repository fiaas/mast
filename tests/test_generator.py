import pytest
from mock import MagicMock

from fiaas_mast.generator import generate_random_uuid_string, Generator
from fiaas_mast.models import Release

APPLICATION_NAME = "test_image"
SPINNAKER_TAGS = {}
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
"""

VALID_DEPLOY_CONFIG_V3_WITH_ANNOTATIONS = """
version: 3
annotations:
    deployment:
        "i_was_here": "first"
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
        "application": "test_image",
        "image": "test_image:a1b2c3d",
        "config": {
            "admin_access": True,
            "healthchecks": {
                "liveness": {
                    "http": {
                        "path": "/healthz"
                    }
                }
            },
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
        },
    }
}

ANNOTATIONS_WITH_SPINNAKER_TAGS = {
    "deployment": {
        "pipeline.schibsted.io/foo": "bar",
        "pipeline.schibsted.io/numeric": "1337",
    },
    "pod": {
        "pipeline.schibsted.io/foo": "bar",
        "pipeline.schibsted.io/numeric": "1337",
    },
    "service": {
        "pipeline.schibsted.io/foo": "bar",
        "pipeline.schibsted.io/numeric": "1337",
    },
    "ingress": {
        "pipeline.schibsted.io/foo": "bar",
        "pipeline.schibsted.io/numeric": "1337",
    },
    "horizontal_pod_autoscaler": {
        "pipeline.schibsted.io/foo": "bar",
        "pipeline.schibsted.io/numeric": "1337",
    },
}

ANNOTATIONS_WITH_MERGED_SPINNAKER_TAGS = {
    "deployment": {
        "i_was_here": "first",
        "pipeline.schibsted.io/foo": "bar",
    },
    "pod": {
        "pipeline.schibsted.io/foo": "bar",
    },
    "service": {
        "pipeline.schibsted.io/foo": "bar",
    },
    "ingress": {
        "pipeline.schibsted.io/foo": "bar",
    },
    "horizontal_pod_autoscaler": {
        "pipeline.schibsted.io/foo": "bar",
    },
}


class TestGeneratePaasbetaApplication(object):
    @pytest.mark.parametrize(
        "config,target_namespace,expected_namespace", ((VALID_DEPLOY_CONFIG_V3, ANY_NAMESPACE, ANY_NAMESPACE),
                                                       (VALID_DEPLOY_CONFIG_V3, "custom-namespace",
                                                        "custom-namespace"),)
    )
    def test_generator_creates_object_of_given_type(self, config, target_namespace, expected_namespace):
        http_client = _given_config_url_response_content_is(config)
        generator = Generator(http_client, create_deployment_id=lambda: DEPLOYMENT_ID)
        returned_paasbeta_application = generator.generate_paasbeta_application(
            target_namespace=target_namespace,
            release=Release(VALID_IMAGE_NAME, VALID_DEPLOY_CONFIG_URL, APPLICATION_NAME, SPINNAKER_TAGS)
        )
        expected_paasbeta_application = BASE_PAASBETA_APPLICATION
        expected_paasbeta_application["metadata"]["namespace"] = expected_namespace
        assert returned_paasbeta_application == expected_paasbeta_application

    def test_generator_adds_spinnaker_annotations(self):
        spinnaker_tags = {'foo': 'bar', 'numeric': 1337}

        http_client = _given_config_url_response_content_is(VALID_DEPLOY_CONFIG_V3)
        generator = Generator(http_client, create_deployment_id=lambda: DEPLOYMENT_ID)
        returned_paasbeta_application = generator.generate_paasbeta_application(
            target_namespace=ANY_NAMESPACE,
            release=Release(VALID_IMAGE_NAME, VALID_DEPLOY_CONFIG_URL, APPLICATION_NAME, spinnaker_tags)
        )
        expected_paasbeta_annotations = ANNOTATIONS_WITH_SPINNAKER_TAGS
        assert returned_paasbeta_application["spec"]["config"]["annotations"] == expected_paasbeta_annotations

    def test_generator_merges_spinnaker_annotations(self):
        spinnaker_tags = {'foo': 'bar'}

        http_client = _given_config_url_response_content_is(VALID_DEPLOY_CONFIG_V3_WITH_ANNOTATIONS)
        generator = Generator(http_client, create_deployment_id=lambda: DEPLOYMENT_ID)
        returned_paasbeta_application = generator.generate_paasbeta_application(
            target_namespace=ANY_NAMESPACE,
            release=Release(VALID_IMAGE_NAME, VALID_DEPLOY_CONFIG_URL, APPLICATION_NAME, spinnaker_tags)
        )
        expected_paasbeta_annotations = ANNOTATIONS_WITH_MERGED_SPINNAKER_TAGS
        assert returned_paasbeta_application["spec"]["config"]["annotations"] == expected_paasbeta_annotations

    def test_generator_without_annotations(self):
        spinnaker_tags = {}

        http_client = _given_config_url_response_content_is(VALID_DEPLOY_CONFIG_V3)
        generator = Generator(http_client, create_deployment_id=lambda: DEPLOYMENT_ID)
        returned_paasbeta_application = generator.generate_paasbeta_application(
            target_namespace=ANY_NAMESPACE,
            release=Release(VALID_IMAGE_NAME, VALID_DEPLOY_CONFIG_URL, APPLICATION_NAME, spinnaker_tags)
        )
        assert "annotations" not in returned_paasbeta_application["spec"]["config"]


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
