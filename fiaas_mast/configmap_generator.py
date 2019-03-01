
from .metadata_generator import MetadataGenerator


class ConfigMapGenerator(MetadataGenerator):

    def generate_configmap(self, target_namespace, configmap_request):
        deployment_id = self.create_deployment_id()
        data = self.download_config(configmap_request.application_data_url)
        metadata = self.metadata(configmap_request, target_namespace, deployment_id)
        configmap_manifest = {
            "apiVersion": "v1",
            "kind": "ConfigMap",
            "metadata": metadata.as_dict(),
            "data": {k: str(v) for k, v in data.items()},
        }
        return deployment_id, configmap_manifest
