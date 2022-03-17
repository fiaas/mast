
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

import yaml
from k8s.models.common import ObjectMeta
from requests.exceptions import MissingSchema, InvalidURL, InvalidSchema

from .common import dict_merge, generate_random_uuid_string, ClientError


class MetadataGenerator:
    def __init__(self, http_client, create_deployment_id=generate_random_uuid_string):
        self.http_client = http_client
        self.create_deployment_id = create_deployment_id

    def build_annotations(self, items, prefix=""):
        annotations = {}
        for k, v, in items:
            annotations["{}{}".format(prefix, k)] = str(v)
        return annotations

    def spinnaker_annotations(self, release):
        return self.build_annotations(release.spinnaker_tags.items(), "pipeline.schibsted.io/")

    def raw_annotations(self, release):
        return self.build_annotations(release.raw_tags.items())

    def raw_labels(self, release):
        return self.build_annotations(release.raw_labels.items())

    def merge_tags(self, generator_object):
        tags = {}
        if generator_object.spinnaker_tags:
            dict_merge(tags, self.spinnaker_annotations(generator_object))

        if generator_object.raw_tags:
            dict_merge(tags, self.raw_annotations(generator_object))

        if generator_object.application_name != generator_object.original_application_name:
            tags['mast'] = {
                'originalApplicationName': generator_object.original_application_name
            }

        return tags

    def merge_labels(self, generator_object):
        labels = {}
        if generator_object.raw_labels:
            dict_merge(labels, self.raw_labels(generator_object))
        return labels

    def metadata(self, generator_object, namespace, deployment_id):
        application_name = generator_object.application_name
        labels = {"fiaas/deployment_id": deployment_id, "app": application_name}
        annotations = {k: str(v) for k, v in generator_object.metadata_annotations.items()}
        # TODO: Why doesn't annotations default to a dict?
        metadata = ObjectMeta(name=application_name, namespace=namespace, labels=labels, annotations=annotations)
        return metadata

    def download_config(self, config_url):
        try:
            resp = self.http_client.get(config_url)
        except (InvalidURL, MissingSchema, InvalidSchema) as e:
            raise ClientError("Invalid config_url: {}".format(config_url)) from e
        resp.raise_for_status()
        try:
            app_config = yaml.safe_load(resp.content)
        except yaml.YAMLError as e:
            raise ClientError("Invalid config YAML: {}".format(e))
        return app_config
