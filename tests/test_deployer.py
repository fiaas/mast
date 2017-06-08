from mock import MagicMock, patch

from schip_spinnaker_webhook.deployer import Deployer
from schip_spinnaker_webhook.models import Release

VALID_IMAGE_NAME = "test_image:a1b2c3d"

NAMESPACE_FROM_ENV = "env_pre"

NAMESPACE_FROM_FILE = "file_pre"

VALID_DEPLOY_CONFIG_URL = "http://url_to_config.file"

TPR_TEMPLATE = """
metadata:
  name: v1beta-example
spec:
  application: v1beta-example
  image: {0}
  config:
{1}
"""

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


class TestCreateDeploymentInK8s(object):
    @patch('requests.get')
    def test_deployer_sends_tpr_to_k8s(self, mock_config):
        config_response = MagicMock()
        config_response.text = VALID_DEPLOY_CONFIG
        mock_config.return_value = config_response

        k8s = MagicMock(spec="k8s.client.Client")
        post = MagicMock()
        k8s.post = post
        namespace = NAMESPACE_FROM_ENV

        Deployer(k8s).deploy(
            namespace=namespace,
            release=Release(VALID_IMAGE_NAME, VALID_DEPLOY_CONFIG_URL)
        )

        mock_config.assert_called_once_with(VALID_DEPLOY_CONFIG_URL)
        post.assert_called_once_with(
            "/apis/schibsted.io/v1beta/namespaces/{0}/paasbetaapplications/".format(NAMESPACE_FROM_ENV),
            TPR_TEMPLATE.format(VALID_IMAGE_NAME, VALID_DEPLOY_CONFIG)
        )
