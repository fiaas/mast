import collections
import uuid

import yaml


def dict_merge(dct, merge_dct):
    """ Recursive dict merge. Inspired by :meth:``dict.update()``, instead of
    updating only top-level keys, dict_merge recurses down into dicts nested
    to an arbitrary depth, updating keys. The ``merge_dct`` is merged into
    ``dct``.
    :param dct: dict onto which the merge is executed
    :param merge_dct: dct merged into dct
    :return: None
    """
    for k, v in merge_dct.items():
        if (k in dct and isinstance(dct[k], dict)
                and isinstance(merge_dct[k], collections.Mapping)):
            dict_merge(dct[k], merge_dct[k])
        else:
            dct[k] = merge_dct[k]


def generate_random_uuid_string():
    id = uuid.uuid4()
    return str(id)


class Generator:
    def __init__(self, http_client, create_deployment_id=generate_random_uuid_string):
        self.http_client = http_client
        self.create_deployment_id = create_deployment_id

    def spinnaker_annotations(self, release):
        annotations = {}
        for k, v, in release.spinnaker_tags.items():
            annotations["pipeline.schibsted.io/{}".format(k)] = v
        return annotations

    def spec(self, release):
        spec = self.download_config(release.config_url)

        spinnaker_annotations = self.spinnaker_annotations(release)

        merge_spec = {
            "image": release.image,
        }

        if spinnaker_annotations:
            merge_spec["annotations"] = {
                "deployment": spinnaker_annotations,
                "pod": spinnaker_annotations,
                "service": spinnaker_annotations,
                "ingress": spinnaker_annotations,
                "horizontal_pod_autoscaler": spinnaker_annotations,
            }

        dict_merge(spec, merge_spec)

        return spec

    def generate_paasbeta_application(self, target_namespace, release):
        """Generate PaasbetaApplication manifest for application"""
        application_name = release.application_name
        spec = self.spec(release)
        namespace = spec["namespace"] if (spec['version'] < 3) and ("namespace" in spec) else target_namespace
        deployment_id = self.create_deployment_id()
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
