#!/usr/bin/env python
# -*- coding: utf-8

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


@pytest.mark.parametrize("expected", ("SUCCESS", "RUNNING", "FAILED"))
def test_get_status(expected, get, status_type):
    def modifier(data):
        data["items"][0]["result"] = expected

    _setup_response(modifier, get, status_type)
    result = status(NAMESPACE, APPLICATION_NAME, DEPLOYMENT_ID)
    assert result.status == expected


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
