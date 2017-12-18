
import logging

from k8s.client import NotFound
from .models import Status
from .paasbeta import PaasbetaStatus
from .fiaas import FiaasStatus


LOGGER = logging.getLogger(__name__)


def status(namespace, application, deployment_id):
    """Get status of a deployment"""
    for model in (PaasbetaStatus, FiaasStatus):
        try:
            search_result = model.find(application, namespace, {"fiaas/deployment_id": deployment_id})
            if len(search_result) > 1:
                LOGGER.warning("Found %d status objects for deployment ID %s", len(search_result), deployment_id)
            status = search_result[-1]
            return Status(status=status.result, info="Deployment of {} is {}".format(application, status.result.lower()))
        except (NotFound, IndexError):
            continue
    return Status(status="UNKNOWN", info="No status for {} found".format(deployment_id))
