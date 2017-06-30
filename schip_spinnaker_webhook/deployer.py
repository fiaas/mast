import uuid

import yaml

from k8s.models.common import ObjectMeta
from .paasbeta import PaasbetaApplication, PaasbetaApplicationSpec


def generate_random_uuid_string():
    id = uuid.uuid4()
    return str(id)


class Deployer:
    def __init__(self, http_client, create_deployment_id=generate_random_uuid_string):
        self.http_client = http_client
        self.create_deployment_id = create_deployment_id

    def deploy(self, namespace, release):
        """Create or update TPR for application"""
        application_name = release.application_name
        config = self.download_config(release.config_url)
        deployment_id = self.create_deployment_id()
        labels = {"fiaas/deployment_id": deployment_id}
        metadata = ObjectMeta(name=application_name, namespace=namespace, labels=labels)
        spec = PaasbetaApplicationSpec(application=application_name, image=release.image, config=config)
        application = PaasbetaApplication.get_or_create(metadata=metadata, spec=spec)
        application.save()

        return application_name, deployment_id

    def download_config(self, config_url):
        resp = self.http_client.get(config_url)
        resp.raise_for_status()
        app_config = yaml.safe_load(resp.text)
        return app_config
