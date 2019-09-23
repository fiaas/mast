
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
