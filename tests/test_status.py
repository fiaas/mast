#!/usr/bin/env python
# -*- coding: utf-8

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


import mock
import os.path
import pytest
import yaml

from fiaas_mast.status import status
from k8s.client import NotFound

NAMESPACE = "somespace"
APPLICATION_NAME = "some_app"
DEPLOYMENT_ID = "some_id"


@pytest.fixture(autouse=True)
def get():
    with mock.patch("k8s.client.Client.get") as m:
        yield m


@pytest.fixture(params=("paasbetastatuses", "statuses", "application-statuses"))
def status_type(request):
    return request.param


@pytest.mark.parametrize("result,logs", (
    ("SUCCESS", []),
    ("RUNNING", []),
    ("FAILED", []),
    ("SUCCESS", ['logline 1', 'logline 2', 'more logs']),
    ("RUNNING", ['logline 1', 'logline 2', 'more logs']),
    ("FAILED", ['logline 1', 'logline 2', 'more logs']),
))
def test_get_status(result, logs, get, status_type):
    def modifier(data):
        data["items"][0]["result"] = result
        data["items"][0]["logs"] = logs

    _setup_response(modifier, get, status_type)
    status_resource = status(NAMESPACE, APPLICATION_NAME, DEPLOYMENT_ID)
    assert status_resource.status == result
    assert status_resource.logs == logs


def test_empty_response(get, status_type):
    def modifier(data):
        data["items"] = []

    _setup_response(modifier, get, status_type)
    result = status(NAMESPACE, APPLICATION_NAME, DEPLOYMENT_ID)
    assert result.status == "UNKNOWN"


def _setup_response(modifier, get, status_type):
    response_file = os.path.join(os.path.dirname(__file__), status_type + ".yml")
    with open(response_file) as fobj:
        response_data = yaml.safe_load(fobj)
        modifier(response_data)
        response = mock.NonCallableMagicMock()
        response.json.return_value = response_data

        def _get(url, **kwargs):
            if url.endswith("{}/".format(status_type)):
                return response
            else:
                raise NotFound()
        get.side_effect = _get
