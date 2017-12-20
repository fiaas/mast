#!/usr/bin/env python
# -*- coding: utf-8

import mock
import os.path
import pytest
import yaml

from fiaas_mast.status import status

NAMESPACE = "somespace"
APPLICATION_NAME = "some_app"
DEPLOYMENT_ID = "some_id"
RESPONSE_FILE = os.path.join(os.path.dirname(__file__), "statuses.yml")


@pytest.fixture(autouse=True)
def get():
    with mock.patch("k8s.client.Client.get") as m:
        yield m


@pytest.mark.parametrize("expected", ("SUCCESS", "RUNNING", "FAILED"))
def test_get_status(expected, get):
    def modifier(data):
        data["items"][0]["result"] = expected

    _setup_response(modifier, get)
    result = status(NAMESPACE, APPLICATION_NAME, DEPLOYMENT_ID)
    assert result.status == expected


def test_empty_response(get):
    def modifier(data):
        data["items"] = []

    _setup_response(modifier, get)
    result = status(NAMESPACE, APPLICATION_NAME, DEPLOYMENT_ID)
    assert result.status == "UNKNOWN"


def _setup_response(modifier, get):
    with open(RESPONSE_FILE) as fobj:
        response_data = yaml.safe_load(fobj)
        modifier(response_data)
        response = mock.NonCallableMagicMock()
        response.json.return_value = response_data
        get.return_value = response
