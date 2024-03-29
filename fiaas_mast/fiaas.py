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

from __future__ import absolute_import

from k8s.base import Model
from k8s.fields import Field, RequiredField, ListField
from k8s.models.common import ObjectMeta


class AdditionalLabelsOrAnnotations(Model):
    _global = Field(dict)
    deployment = Field(dict)
    horizontal_pod_autoscaler = Field(dict)
    ingress = Field(dict)
    service = Field(dict)
    pod = Field(dict)
    status = Field(dict)


class FiaasApplicationSpec(Model):
    application = RequiredField(str)
    image = RequiredField(str)
    config = RequiredField(dict)
    additional_labels = Field(AdditionalLabelsOrAnnotations)
    additional_annotations = Field(AdditionalLabelsOrAnnotations)


class FiaasApplication(Model):
    class Meta:
        url_template = "/apis/fiaas.schibsted.io/v1/namespaces/{namespace}/applications/{name}"
        watch_list_url = "/apis/fiaas.schibsted.io/v1/watch/applications"

    # Workaround for https://github.com/kubernetes/kubernetes/issues/44182
    apiVersion = Field(str, "fiaas.schibsted.io/v1")
    kind = Field(str, "Application")

    metadata = Field(ObjectMeta)
    spec = Field(FiaasApplicationSpec)


class FiaasStatus(Model):
    """Deprecated. This model will be removed as soon as migration to ApplicationStatus is complete"""
    class Meta:
        url_template = "/apis/fiaas.schibsted.io/v1/namespaces/{namespace}/statuses/{name}"

    # Workaround for https://github.com/kubernetes/kubernetes/issues/44182
    apiVersion = Field(str, "fiaas.schibsted.io/v1")
    kind = Field(str, "Status")

    metadata = Field(ObjectMeta)
    result = Field(str)
    logs = ListField(str)


class FiaasApplicationStatus(Model):
    class Meta:
        url_template = "/apis/fiaas.schibsted.io/v1/namespaces/{namespace}/application-statuses/{name}"

    # Workaround for https://github.com/kubernetes/kubernetes/issues/44182
    apiVersion = Field(str, "fiaas.schibsted.io/v1")
    kind = Field(str, "ApplicationStatus")

    metadata = Field(ObjectMeta)
    result = Field(str)
    logs = ListField(str)
