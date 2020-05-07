
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

from .common import check_models, generate_random_uuid_string, ClientError
from .metadata_generator import MetadataGenerator


class ApplicationGenerator(MetadataGenerator):
    def __init__(self, http_client, create_deployment_id=generate_random_uuid_string):
        super().__init__(http_client, create_deployment_id)
        self.application_model, self.spec_model = check_models()

    def generate_application(self, target_namespace, release):
        """Generate Application manifest for application"""
        spec = self.spec(release)
        deployment_id = self.create_deployment_id()
        config = spec.config
        namespace = config["namespace"] if (config['version'] < 3) and ("namespace" in config) else target_namespace
        metadata = self.metadata(release, namespace, deployment_id)
        application = self.application_model(metadata=metadata, spec=spec)
        return deployment_id, application

    def spec(self, release):
        config = self.download_config(release.config_url)
        if not config:
            raise ClientError("Invalid config: {}".format(release.config_url))

        global_tags = {"global": super().merge_tags(release)}

        global_labels = {"global": super().merge_labels(release)}

        spec = self.spec_model(image=release.image, application=release.application_name, config=config,
                               additional_annotations=global_tags, additional_labels=global_labels)
        return spec
