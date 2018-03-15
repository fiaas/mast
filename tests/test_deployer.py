import pytest
import yaml
from k8s.client import NotFound
from k8s.models.common import ObjectMeta
from mock import MagicMock, patch

from fiaas_mast.deployer import generate_random_uuid_string, Deployer, select_models, DeployerError
from fiaas_mast.fiaas import FiaasApplicationSpec, FiaasApplication
from fiaas_mast.models import Release
from fiaas_mast.paasbeta import PaasbetaApplicationSpec, PaasbetaApplication

APPLICATION_NAME = "test_image"
SPINNAKER_TAGS = {}
DEPLOYMENT_ID = "deadbeef-abba-cafe-1337-baaaaaaaaaad"
VALID_IMAGE_NAME = "test_image:a1b2c3d"
VALID_DEPLOY_CONFIG_URL = "http://url_to_config.file"
ANY_NAMESPACE = "any-namespace"

VALID_DEPLOY_CONFIG = """
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

VALID_DEPLOY_CONFIG_WITH_NAMESPACE = """
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

VALID_DEPLOY_CONFIG_WITH_NAMESPACE_V3 = """
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


class TestCreateDeploymentInK8s(object):
    @pytest.fixture(params=["fiaas", "paasbeta"])
    def object_types(self, request):
        if request.param == "fiaas":
            return FiaasApplication, FiaasApplicationSpec
        if request.param == "paasbeta":
            return PaasbetaApplication, PaasbetaApplicationSpec

    @pytest.fixture
    def k8s_model(self):
        k8s_model = MagicMock()
        k8s_model.save = MagicMock()
        return k8s_model

    @pytest.fixture
    def get_or_create(self, k8s_model):
        with patch('k8s.base.ApiMixIn.get_or_create') as m:
            m.return_value = k8s_model
            yield m

    @pytest.fixture(autouse=True)
    def select_models(self, object_types):
        with patch('fiaas_mast.deployer.select_models') as m:
            m.return_value = object_types
            yield m

    @pytest.mark.parametrize("config,target_namespace,expected_namespace", (
            (VALID_DEPLOY_CONFIG, ANY_NAMESPACE, ANY_NAMESPACE),
            (VALID_DEPLOY_CONFIG_WITH_NAMESPACE, ANY_NAMESPACE, "custom-namespace"),
            (VALID_DEPLOY_CONFIG_WITH_NAMESPACE_V3, "target-namespace", "target-namespace"),
    ))
    def test_deployer_creates_object_of_given_type(self,
                                                   get_or_create,
                                                   k8s_model,
                                                   object_types,
                                                   config,
                                                   target_namespace,
                                                   expected_namespace):
        http_client = _given_config_url_response_content_is(config)
        application_model, spec_model = object_types
        deployer = Deployer(http_client, create_deployment_id=lambda: DEPLOYMENT_ID)
        returned_namespace, returned_name, returned_id = deployer.deploy(
            target_namespace=target_namespace,
            release=Release(
                VALID_IMAGE_NAME,
                VALID_DEPLOY_CONFIG_URL,
                APPLICATION_NAME,
                APPLICATION_NAME,
                SPINNAKER_TAGS
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
        get_or_create.assert_called_once_with(metadata=metadata, spec=spec)
        assert isinstance(get_or_create.call_args_list[-1][-1]["spec"], spec_model)
        k8s_model.save.assert_called_once()


class TestUUID:
    def test_uuid_generation(self):
        uuid1 = generate_random_uuid_string()
        uuid2 = generate_random_uuid_string()
        assert uuid1 != uuid2


class TestSelectModel:
    @pytest.fixture(params=(True, False))
    def crd(self, request):
        with patch('fiaas_mast.fiaas.FiaasApplication.list') as fm:
            fm.side_effect = None if request.param else NotFound()
            yield request.param

    @pytest.fixture(params=(True, False))
    def tpr(self, request):
        with patch('fiaas_mast.paasbeta.PaasbetaApplication.list') as pm:
            pm.side_effect = None if request.param else NotFound()
            yield request.param

    def test_select_models(self, crd, tpr):
        if not crd and not tpr:
            with pytest.raises(DeployerError):
                select_models()
            return

        if crd:
            wanted_app, wanted_spec = FiaasApplication, FiaasApplicationSpec
        else:
            wanted_app, wanted_spec = PaasbetaApplication, PaasbetaApplicationSpec
        actual_app, actual_spec = select_models()
        assert wanted_app == actual_app
        assert wanted_spec == actual_spec


def _given_config_url_response_content_is(config):
    http_client = MagicMock(spec="requests.Session")
    config_response = MagicMock()
    config_response.text = config

    http_client_get = MagicMock()
    http_client_get.return_value = config_response
    http_client.get = http_client_get

    return http_client
