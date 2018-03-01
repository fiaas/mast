import logging

import yaml

from k8s.client import NotFound
from k8s.models.common import ObjectMeta

from .paasbeta import PaasbetaApplication, PaasbetaApplicationSpec
from .fiaas import FiaasApplication, FiaasApplicationSpec
from .common import generate_random_uuid_string

LOG = logging.getLogger(__name__)


def select_models():
    for app_model, spec_model in (
            (FiaasApplication, FiaasApplicationSpec),
            (PaasbetaApplication, PaasbetaApplicationSpec),
    ):
        try:
            app_model.list()
            return app_model, spec_model
        except NotFound:
            LOG.debug("{} was not found".format(app_model))
    raise DeployerError("Unable to find support for either PaasbetaApplication or FiaasApplication in the cluster")


class Deployer:
    def __init__(self, http_client, create_deployment_id=generate_random_uuid_string):
        self.http_client = http_client
        self.create_deployment_id = create_deployment_id
        self.application_model, self.spec_model = select_models()

    def deploy(self, target_namespace, release):
        """Create or update TPR for application"""
        application_name = release.application_name
        config = self.download_config(release.config_url)
        namespace = config["namespace"] if (config['version'] < 3) and ("namespace" in config) else target_namespace
        deployment_id = self.create_deployment_id()
        labels = {"fiaas/deployment_id": deployment_id, "app": application_name}
        metadata = ObjectMeta(name=application_name, namespace=namespace, labels=labels)
        spec = self.spec_model(application=application_name, image=release.image, config=config)
        application = self.application_model.get_or_create(metadata=metadata, spec=spec)
        application.save()

        return namespace, application_name, deployment_id

    def download_config(self, config_url):
        resp = self.http_client.get(config_url)
        resp.raise_for_status()
        app_config = yaml.safe_load(resp.text)
        return app_config


class DeployerError(Exception):
    pass
