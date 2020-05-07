
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

import mock
import pytest
from mock import MagicMock

from fiaas_mast.application_generator import ApplicationGenerator
from fiaas_mast.common import generate_random_uuid_string
from fiaas_mast.common import make_safe_name
from fiaas_mast.common import ClientError
from fiaas_mast.configmap_generator import ConfigMapGenerator
from fiaas_mast.models import Release, ApplicationConfiguration
from fiaas_mast.fiaas import FiaasApplication, FiaasApplicationSpec

APPLICATION_NAME = "test-image"
SPINNAKER_TAGS = {}
DEPLOYMENT_ID = "deadbeef-abba-cafe-1337-baaaaaaaaaad"
VALID_IMAGE_NAME = "test_image:a1b2c3d"
VALID_DEPLOY_CONFIG_URL = "http://url_to_config.file"
VALID_CONFIGMAP_URL = "http://url_to_configmap.file"
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

BASE_CONFIGMAP = {
    "data": {
        "rules.yml": "# put your recording rules here",
        "int_variable": "42",
        "float_variable": "3.14",
        "boolean_variable": "True"
    },
    "kind": "ConfigMap",
    "apiVersion": "v1",
    "metadata": {
        "finalizers": [],
        "annotations": {
            "strategy.spinnaker.io/versioned": "false"
        },
        "labels": {
            "app": "test-image",
            "fiaas/deployment_id": "deadbeef-abba-cafe-1337-baaaaaaaaaad"
        },
        "name": "test-image",
        "namespace": "any-namespace",
        "ownerReferences": []
    }
}

APPLICATION_DATA = """
rules.yml: '# put your recording rules here'
int_variable: 42
float_variable: 3.14
boolean_variable: True
"""

EMPTY_BASE_CONFIGMAP = {
    "data": {
    },
    "kind": "ConfigMap",
    "apiVersion": "v1",
    "metadata": {
        "finalizers": [],
        "annotations": {
            "strategy.spinnaker.io/versioned": "false"
        },
        "labels": {
            "app": "test-image",
            "fiaas/deployment_id": "deadbeef-abba-cafe-1337-baaaaaaaaaad"
        },
        "name": "test-image",
        "namespace": "any-namespace",
        "ownerReferences": []
    }
}

EMPTY_APPLICATION_DATA = """
"""

FIAAS_APPLICATION = {
    "apiVersion": "fiaas.schibsted.io/v1",
    "kind": "Application",
    "metadata": {
        "finalizers": [],
        "labels": {
            "app": "test-image",
            "fiaas/deployment_id": "deadbeef-abba-cafe-1337-baaaaaaaaaad"
        },
        "name": "test-image",
        "namespace": "target-namespace",
        "ownerReferences": []
    },
    "spec": {
        "application": "test-image",
        "image": "test_image:a1b2c3d",
        "additional_labels": {
            "global": {}
        },
        "additional_annotations": {
            "global": {}
        },
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
    "additional_annotations": {
        "global": {
            "pipeline.schibsted.io/foo": "bar",
            "pipeline.schibsted.io/numeric": "1337",
        }
    },
    "additional_labels": {"global": {}}
}

ANNOTATIONS_WITH_RAW_TAGS = {
    "additional_annotations": {
        "global": {
            "my_domain.io/some_annotation": "and_some_value",
            "my_domain_aux.io/some_annotation": "and_some_value"
        }
    },
    "additional_labels": {"global": {}}
}

ANNOTATIONS_WITH_RAW_LABELS = {
    "additional_annotations": {"global": {}},
    "additional_labels": {
        "global": {
            "my_domain.io/some_label": "and_some_value",
            "my_domain.io/some_other_label": "and_some_other_value"
        }
    }
}

ANNOTATIONS_WITH_MERGED_SPINNAKER_TAGS = {
    "additional_annotations": {
        "global": {
            "pipeline.schibsted.io/foo": "bar",
        }
    },
    "additional_labels": {"global": {}}
}

ANNOTATIONS_WITH_MERGED_SPINNAKER_TAGS_AND_RAW_TAGS = {
    "additional_annotations": {
        "global": {
            "pipeline.schibsted.io/foo": "bar",
            'my_domain.io/some_annotation': 'and_some_value'
        }
    },
    "additional_labels": {"global": {}}
}

ANNOTATIONS_WITH_MERGED_RAW_TAGS = {
    "additional_annotations": {
        "global": {
            'my_domain.io/some_annotation': 'and_some_value'
        }
    },
    "additional_labels": {"global": {}}
}


class TestApplicationGenerator(object):
    @pytest.fixture(autouse=True)
    def check_models(self):
        with mock.patch('fiaas_mast.application_generator.check_models') as m:
            m.return_value = (FiaasApplication, FiaasApplicationSpec)
            yield m

    @pytest.mark.parametrize(
        "config,target_namespace,expected_namespace", ((VALID_DEPLOY_CONFIG_V3, ANY_NAMESPACE, ANY_NAMESPACE),
                                                       (VALID_DEPLOY_CONFIG_V3, "custom-namespace",
                                                        "custom-namespace"),)
    )
    def test_generator_creates_object_of_given_type(self, config, target_namespace, expected_namespace):
        spinnaker_tags = {}
        raw_tags = {}
        raw_labels = {}

        http_client = _given_config_url_response_content_is(config)
        generator = ApplicationGenerator(http_client, create_deployment_id=lambda: DEPLOYMENT_ID)
        deployment_id, returned_paasbeta_application = generator.generate_application(
            target_namespace=target_namespace,
            release=Release(
                VALID_IMAGE_NAME,
                VALID_DEPLOY_CONFIG_URL,
                make_safe_name(APPLICATION_NAME),
                APPLICATION_NAME,
                spinnaker_tags,
                raw_tags,
                raw_labels,
                {}
            )
        )
        expected_paasbeta_application = FIAAS_APPLICATION
        expected_paasbeta_application["metadata"]["namespace"] = expected_namespace

        assert returned_paasbeta_application.as_dict() == expected_paasbeta_application

    @pytest.mark.parametrize(
        "config,target_namespace,expected_namespace", ((VALID_DEPLOY_CONFIG_V3, ANY_NAMESPACE, ANY_NAMESPACE),
                                                       (VALID_DEPLOY_CONFIG_V3, "custom-namespace",
                                                        "custom-namespace"),)
    )
    def test_generator_annotates_moniker_application(self, config, target_namespace, expected_namespace):
        spinnaker_tags = {}
        raw_tags = {}
        raw_labels = {}
        metadata_annotation = {
            "moniker.spinnaker.io/application": "unicorn",
            "this_is_a_number": 3,
            "this_is_a_floating_point_number": 3.14,
            "this_is_a_bool": True,
        }

        expected_metadata_annotations = {
            "moniker.spinnaker.io/application": "unicorn",
            "this_is_a_number": "3",
            "this_is_a_floating_point_number": "3.14",
            "this_is_a_bool": "True",
        }

        http_client = _given_config_url_response_content_is(config)
        generator = ApplicationGenerator(http_client, create_deployment_id=lambda: DEPLOYMENT_ID)
        deployment_id, returned_application = generator.generate_application(
            target_namespace=target_namespace,
            release=Release(
                VALID_IMAGE_NAME,
                VALID_DEPLOY_CONFIG_URL,
                make_safe_name(APPLICATION_NAME),
                APPLICATION_NAME,
                spinnaker_tags,
                raw_tags,
                raw_labels,
                metadata_annotation
            )
        )
        expected_application = FIAAS_APPLICATION
        expected_application["metadata"]["namespace"] = expected_namespace
        expected_application["metadata"]["annotations"] = expected_metadata_annotations

        assert returned_application.as_dict() == expected_application

    def test_generator_adds_spinnaker_annotations(self):
        spinnaker_tags = {'foo': 'bar', 'numeric': 1337}
        raw_tags = {}
        raw_labels = {}

        self._annotations_verification(spinnaker_tags, raw_tags, raw_labels, ANNOTATIONS_WITH_SPINNAKER_TAGS,
                                       VALID_DEPLOY_CONFIG_V3)

    def test_generator_adds_raw_annotations(self):
        spinnaker_tags = {}
        raw_tags = {'my_domain.io/some_annotation': 'and_some_value',
                    'my_domain_aux.io/some_annotation': 'and_some_value'}
        raw_labels = {}

        self._annotations_verification(spinnaker_tags, raw_tags, raw_labels, ANNOTATIONS_WITH_RAW_TAGS,
                                       VALID_DEPLOY_CONFIG_V3)

    def test_generator_adds_raw_labels(self):
        spinnaker_tags = {}
        raw_tags = {}
        raw_labels = {
            'my_domain.io/some_label': 'and_some_value',
            'my_domain.io/some_other_label': 'and_some_other_value'
        }

        self._annotations_verification(spinnaker_tags, raw_tags, raw_labels, ANNOTATIONS_WITH_RAW_LABELS,
                                       VALID_DEPLOY_CONFIG_V3)

    def test_generator_merges_spinnaker_annotations(self):
        spinnaker_tags = {'foo': 'bar'}
        raw_tags = {}
        raw_labels = {}

        self._annotations_verification(spinnaker_tags, raw_tags, raw_labels, ANNOTATIONS_WITH_MERGED_SPINNAKER_TAGS,
                                       VALID_DEPLOY_CONFIG_V3_WITH_ANNOTATIONS)

    def test_generator_merges_raw_annotations(self):
        spinnaker_tags = {}
        raw_tags = {'my_domain.io/some_annotation': 'and_some_value'}
        raw_labels = {}

        self._annotations_verification(spinnaker_tags, raw_tags, raw_labels, ANNOTATIONS_WITH_MERGED_RAW_TAGS,
                                       VALID_DEPLOY_CONFIG_V3_WITH_ANNOTATIONS)

    def test_generator_merges_spinnaker_and_raw_annotations(self):
        spinnaker_tags = {'foo': 'bar'}
        raw_tags = {'my_domain.io/some_annotation': 'and_some_value'}
        raw_labels = {}

        self._annotations_verification(spinnaker_tags, raw_tags, raw_labels,
                                       ANNOTATIONS_WITH_MERGED_SPINNAKER_TAGS_AND_RAW_TAGS,
                                       VALID_DEPLOY_CONFIG_V3_WITH_ANNOTATIONS)

    def _annotations_verification(self, spinnaker_tags, raw_tags, raw_labels, exptected_paasbeta_result, deploy_config):
        http_client = _given_config_url_response_content_is(deploy_config)
        generator = ApplicationGenerator(http_client, create_deployment_id=lambda: DEPLOYMENT_ID)
        deployment_id, returned_paasbeta_application = generator.generate_application(
            target_namespace=ANY_NAMESPACE,
            release=Release(
                VALID_IMAGE_NAME,
                VALID_DEPLOY_CONFIG_URL,
                make_safe_name(APPLICATION_NAME),
                APPLICATION_NAME,
                spinnaker_tags,
                raw_tags,
                raw_labels,
                {}
            )
        )
        returned_annotations = {
            'additional_annotations': returned_paasbeta_application.spec.additional_annotations,
            'additional_labels': returned_paasbeta_application.spec.additional_labels,
        }
        assert returned_annotations == exptected_paasbeta_result

    def test_generator_without_annotations(self):
        spinnaker_tags = {}
        raw_tags = {}
        raw_labels = {}

        http_client = _given_config_url_response_content_is(VALID_DEPLOY_CONFIG_V3)
        generator = ApplicationGenerator(http_client, create_deployment_id=lambda: DEPLOYMENT_ID)
        deployment_id, returned_paasbeta_application = generator.generate_application(
            target_namespace=ANY_NAMESPACE,
            release=Release(
                VALID_IMAGE_NAME,
                VALID_DEPLOY_CONFIG_URL,
                make_safe_name(APPLICATION_NAME),
                APPLICATION_NAME,
                spinnaker_tags,
                raw_tags,
                raw_labels,
                {}
            )
        )
        assert "annotations" not in returned_paasbeta_application.spec.config

    def test_generator_with_app_name_bad_chars(self):
        app_name_with_underscores = "test_app"
        spinnaker_tags = {}
        raw_tags = {}
        raw_labels = {}

        http_client = _given_config_url_response_content_is(VALID_DEPLOY_CONFIG_V3)
        generator = ApplicationGenerator(http_client, create_deployment_id=lambda: DEPLOYMENT_ID)
        deployment_id, returned_application = generator.generate_application(
            target_namespace=ANY_NAMESPACE,
            release=Release(
                VALID_IMAGE_NAME,
                VALID_DEPLOY_CONFIG_URL,
                make_safe_name(app_name_with_underscores),
                app_name_with_underscores,
                spinnaker_tags,
                raw_tags,
                raw_labels,
                {}
            )
        )

        returned_metadata = returned_application.metadata
        assert returned_metadata.name == make_safe_name(app_name_with_underscores)
        assert returned_metadata.labels["app"] == make_safe_name(app_name_with_underscores)
        returned_spec = returned_application.spec
        assert returned_spec.application == make_safe_name(app_name_with_underscores)
        assert returned_spec.additional_annotations[
            "global"]["mast"]["originalApplicationName"] == app_name_with_underscores

    def test_generator_with_empty_config(self):
        spinnaker_tags = {}
        raw_tags = {}
        raw_labels = {}

        http_client = _given_config_url_response_content_is("")
        generator = ApplicationGenerator(http_client, create_deployment_id=lambda: DEPLOYMENT_ID)

        with pytest.raises(ClientError):
            deployment_id, returned_application = generator.generate_application(
                target_namespace=ANY_NAMESPACE,
                release=Release(
                    VALID_IMAGE_NAME,
                    VALID_DEPLOY_CONFIG_URL,
                    make_safe_name(APPLICATION_NAME),
                    APPLICATION_NAME,
                    spinnaker_tags,
                    raw_tags,
                    raw_labels,
                    {}
                )
            )


class TestConfigMapGenerator(object):
    def test_configmap_generator(self):
        spinnaker_tags = {}
        raw_tags = {}
        metadata_annotations = {'strategy.spinnaker.io/versioned': 'false'}

        http_client = _given_config_url_response_content_is(APPLICATION_DATA)
        generator = ConfigMapGenerator(http_client, create_deployment_id=lambda: DEPLOYMENT_ID)
        deployment_id, returned_configmap = generator.generate_configmap(
            target_namespace=ANY_NAMESPACE,
            configmap_request=ApplicationConfiguration(
                APPLICATION_DATA,
                make_safe_name(APPLICATION_NAME),
                APPLICATION_NAME,
                spinnaker_tags,
                raw_tags,
                metadata_annotations
            )
        )
        expected_configmap = BASE_CONFIGMAP
        expected_configmap["metadata"]["namespace"] = ANY_NAMESPACE
        assert returned_configmap == expected_configmap

    def test_empty_configmap_generator(self):
        spinnaker_tags = {}
        raw_tags = {}
        metadata_annotations = {'strategy.spinnaker.io/versioned': 'false'}

        http_client = _given_config_url_response_content_is(EMPTY_APPLICATION_DATA)
        generator = ConfigMapGenerator(http_client, create_deployment_id=lambda: DEPLOYMENT_ID)
        deployment_id, returned_configmap = generator.generate_configmap(
            target_namespace=ANY_NAMESPACE,
            configmap_request=ApplicationConfiguration(
                EMPTY_APPLICATION_DATA,
                make_safe_name(APPLICATION_NAME),
                APPLICATION_NAME,
                spinnaker_tags,
                raw_tags,
                metadata_annotations
            )
        )
        expected_configmap = EMPTY_BASE_CONFIGMAP
        expected_configmap["metadata"]["namespace"] = ANY_NAMESPACE
        assert returned_configmap == expected_configmap


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
