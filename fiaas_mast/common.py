import collections
import logging
import uuid

from k8s.client import NotFound

from fiaas_mast.fiaas import FiaasApplication, FiaasApplicationSpec
from fiaas_mast.paasbeta import PaasbetaApplication, PaasbetaApplicationSpec

LOG = logging.getLogger(__name__)


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


def make_safe_name(name):
    safe_name = name.replace('_', '-')
    return safe_name


def select_models():
    for app_model, spec_model in (
            (FiaasApplication, FiaasApplicationSpec),
            (PaasbetaApplication, PaasbetaApplicationSpec),
    ):
        try:
            app_model.list()
            return app_model, spec_model
        except NotFound:
            LOG.debug("{} was not found".format(app_model))
    raise PlatformError("Unable to find support for either PaasbetaApplication or FiaasApplication in the cluster")


class ClientError(Exception):
    def __init__(self, description, *args, **kwargs):
        self.code = 422
        self.name = "Unprocessable Entity"
        self.description = description


class PlatformError(Exception):
    pass
