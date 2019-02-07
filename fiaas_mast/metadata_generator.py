import yaml
from k8s.models.common import ObjectMeta
from requests.exceptions import MissingSchema, InvalidURL

from .common import dict_merge, generate_random_uuid_string, ClientError


class MetadataGenerator:
    def __init__(self, http_client, create_deployment_id=generate_random_uuid_string):
        self.http_client = http_client
        self.create_deployment_id = create_deployment_id

    def build_annotations(self, items, prefix=""):
        annotations = {}
        for k, v, in items:
            annotations["{}{}".format(prefix, k)] = str(v)
        annotation_objects = self.get_annotation_objects()
        return {k: annotations for k in annotation_objects} if annotation_objects else annotations

    def spinnaker_annotations(self, release):
        return self.build_annotations(release.spinnaker_tags.items(), "pipeline.schibsted.io/")

    def raw_annotations(self, release):
        return self.build_annotations(release.raw_tags.items())

    def merge_tags(self, generator_object, config):
        if generator_object.spinnaker_tags:
            if "annotations" not in config:
                config["annotations"] = {}
            dict_merge(config["annotations"], self.spinnaker_annotations(generator_object))

        if generator_object.raw_tags:
            if "annotations" not in config:
                config["annotations"] = {}
            dict_merge(config["annotations"], self.raw_annotations(generator_object))

        if generator_object.application_name != generator_object.original_application_name:
            if "annotations" not in config:
                config["annotations"] = {}

            config['annotations']['mast'] = {
                'originalApplicationName': generator_object.original_application_name
            }

    def metadata(self, generator_object, namespace, deployment_id):
        application_name = generator_object.application_name
        labels = {"fiaas/deployment_id": deployment_id, "app": application_name}
        # TODO: Why doesn't annotations default to a dict?
        metadata = ObjectMeta(name=application_name, namespace=namespace, labels=labels, annotations={})

        if generator_object.spinnaker_tags:
            metadata.annotations = self.spinnaker_annotations(generator_object)

        if generator_object.raw_tags:
            dict_merge(metadata.annotations, self.raw_annotations(generator_object))

        return metadata

    def get_annotation_objects(self):
        return []

    def download_config(self, config_url):
        try:
            resp = self.http_client.get(config_url)
        except (InvalidURL, MissingSchema) as e:
            raise ClientError("Invalid config_url") from e
        resp.raise_for_status()
        app_config = yaml.safe_load(resp.text)
        return app_config
