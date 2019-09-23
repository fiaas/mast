
# Copyright 2017-2019 The FIAAS Authors
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.


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
            "data": {k: str(v) for k, v in data.items()} if data else {},
        }
        return deployment_id, configmap_manifest
