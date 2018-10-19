from k8s.models.configmap import ConfigMap

from .metadata_generator import MetadataGenerator


class ConfigMapGenerator(MetadataGenerator):

    def generate_configmap(self, target_namespace, configmap_request):
        deployment_id = self.create_deployment_id()
        data = self.download_config(configmap_request.application_data_url)
        metadata = self.metadata(configmap_request, target_namespace, deployment_id)
        config_map = ConfigMap(metadata=metadata, data=data)
        return deployment_id, config_map
