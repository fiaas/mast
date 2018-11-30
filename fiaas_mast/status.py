import logging

from k8s.client import NotFound

from .fiaas import FiaasStatus, FiaasApplicationStatus
from .models import Status
from .paasbeta import PaasbetaStatus

LOGGER = logging.getLogger(__name__)


def status(namespace, application, deployment_id):
    """Get status of a deployment"""
    for model in (PaasbetaStatus, FiaasStatus, FiaasApplicationStatus):
        try:
            search_result = model.find(application, namespace, {"fiaas/deployment_id": deployment_id})
            if len(search_result) > 1:
                LOGGER.warning("Found %d status objects for deployment ID %s", len(search_result), deployment_id)
            s = search_result[-1]
            return Status(status=s.result, info="Deployment of {} is {}".format(application, s.result.lower()),
                          logs=s.logs)
        except (NotFound, IndexError):
            continue
    return Status(status="UNKNOWN", info="No status for {} found".format(deployment_id), logs=[])
