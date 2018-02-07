import uuid

import yaml


def generate_random_uuid_string():
    id = uuid.uuid4()
    return str(id)


class Generator:
    def __init__(self, http_client, create_deployment_id=generate_random_uuid_string):
        self.http_client = http_client
        self.create_deployment_id = create_deployment_id

    def generate_paasbeta_application(self, target_namespace, release):
        """Generate PaasbetaApplication manifest for application"""
        application_name = release.application_name
        spec = self.download_config(release.config_url)
        namespace = spec["namespace"] if (spec['version'] < 3) and ("namespace" in spec) else target_namespace
        deployment_id = self.create_deployment_id()
        spec["image"] = release.image
        labels = {"fiaas/deployment_id": deployment_id, "app": application_name}
        metadata = {"labels": labels, "name": application_name, "namespace": namespace}
        manifest = {
            "apiVersion": "schibsted.io/v1beta",
            "kind": "PaasbetaApplication",
            "metadata": metadata,
            "spec": spec
        }
        return manifest

    def download_config(self, config_url):
        resp = self.http_client.get(config_url)
        resp.raise_for_status()
        app_config = yaml.safe_load(resp.text)
        return app_config
