from .metadata_generator import MetadataGenerator


class PaasBetaApplicationGenerator(MetadataGenerator):

    def generate_paasbeta_application(self, target_namespace, release):
        """Generate PaasbetaApplication manifest for application"""
        spec = self.spec(release)
        deployment_id = self.create_deployment_id()
        config = spec["config"]
        namespace = config["namespace"] if (config['version'] < 3) and ("namespace" in config) else target_namespace
        metadata = self.metadata(release, namespace, deployment_id)
        manifest = {
            "apiVersion": "schibsted.io/v1beta",
            "kind": "PaasbetaApplication",
            "metadata": metadata,
            "spec": spec
        }
        return deployment_id, manifest

    def spec(self, release):
        config = self.download_config(release.config_url)

        super().merge_tags(release, config)

        spec = {
            "image": release.image,
            "application": release.application_name,
            "config": config
        }

        return spec

    def get_annotation_objects(self):
        return ["deployment", "pod", "service", "ingress", "horizontal_pod_autoscaler"]
