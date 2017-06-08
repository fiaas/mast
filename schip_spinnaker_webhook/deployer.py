import yaml

from k8s.models.common import ObjectMeta
from .paasbetaapplication import PaasbetaApplication, PaasbetaApplicationSpec


class Deployer:
    def __init__(self, http_client):
        self.http_client = http_client

    def deploy(self, namespace, release):
        """Create or update TPR for application"""
        application_name = release.image.split(":")[0]
        config = self.download_config(release.config_url)
        labels = {}
        metadata = ObjectMeta(name=application_name, namespace=namespace, labels=labels)
        spec = PaasbetaApplicationSpec(application=application_name, image=release.image, config=config)
        application = PaasbetaApplication.get_or_create(metadata=metadata, spec=spec)
        application.save()

        return True

    def download_config(self, config_url):
        resp = self.http_client.get(config_url)
        resp.raise_for_status()
        app_config = yaml.safe_load(resp.text)
        return app_config
