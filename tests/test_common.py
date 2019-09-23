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

import pytest
from k8s.client import NotFound
from mock import patch

from fiaas_mast.common import select_models, PlatformError
from fiaas_mast.fiaas import FiaasApplication, FiaasApplicationSpec
from fiaas_mast.paasbeta import PaasbetaApplication, PaasbetaApplicationSpec


class TestSelectModel:
    @pytest.fixture(params=(True, False))
    def crd(self, request):
        with patch('fiaas_mast.fiaas.FiaasApplication.list') as fm:
            fm.side_effect = None if request.param else NotFound()
            yield request.param

    @pytest.fixture(params=(True, False))
    def tpr(self, request):
        with patch('fiaas_mast.paasbeta.PaasbetaApplication.list') as pm:
            pm.side_effect = None if request.param else NotFound()
            yield request.param

    def test_select_models(self, crd, tpr):
        if not crd and not tpr:
            with pytest.raises(PlatformError):
                select_models()
            return

        if crd:
            wanted_app, wanted_spec = FiaasApplication, FiaasApplicationSpec
        else:
            wanted_app, wanted_spec = PaasbetaApplication, PaasbetaApplicationSpec
        actual_app, actual_spec = select_models()
        assert wanted_app == actual_app
        assert wanted_spec == actual_spec
