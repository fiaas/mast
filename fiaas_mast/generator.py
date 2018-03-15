import yaml

from .common import dict_merge, generate_random_uuid_string


class Generator:
    def __init__(self, http_client, create_deployment_id=generate_random_uuid_string):
        self.http_client = http_client
        self.create_deployment_id = create_deployment_id

    def spinnaker_annotations(self, release):
        annotations = {}
        for k, v, in release.spinnaker_tags.items():
            annotations["pipeline.schibsted.io/{}".format(k)] = str(v)
        objects = ["deployment", "pod", "service", "ingress", "horizontal_pod_autoscaler"]
        return {k: annotations for k in objects}

    def spec(self, release):
        config = self.download_config(release.config_url)

        if release.spinnaker_tags:
            if "annotations" not in config:
                config["annotations"] = {}
            dict_merge(config["annotations"], self.spinnaker_annotations(release))

        if release.application_name != release.original_application_name:
            if "annotations" not in config:
                config["annotations"] = {}

            config['annotations']['mast'] = {
                'originalApplicationName': release.original_application_name
            }

        spec = {
            "image": release.image,
            "application": release.application_name,
            "config": config
        }

        return spec

    def metadata(self, release, spec, target_namespace, deployment_id):
        application_name = release.application_name
        labels = {"fiaas/deployment_id": deployment_id, "app": application_name}

        config = spec["config"]
        namespace = config["namespace"] if (config['version'] < 3) and ("namespace" in config) else target_namespace

        metadata = {"labels": labels, "name": application_name, "namespace": namespace}

        if release.spinnaker_tags:
            metadata["annotations"] = self.spinnaker_annotations(release)

        return metadata

    def generate_paasbeta_application(self, target_namespace, release):
        """Generate PaasbetaApplication manifest for application"""
        spec = self.spec(release)
        deployment_id = self.create_deployment_id()
        metadata = self.metadata(release, spec, target_namespace, deployment_id)
        manifest = {
            "apiVersion": "schibsted.io/v1beta",
            "kind": "PaasbetaApplication",
            "metadata": metadata,
            "spec": spec
        }
        body = {
            "manifest": manifest,
            "deployment_id": deployment_id
        }
        return body

    def download_config(self, config_url):
        resp = self.http_client.get(config_url)
        resp.raise_for_status()
        app_config = yaml.safe_load(resp.text)
        return app_config
