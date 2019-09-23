
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

from collections import namedtuple

Release = namedtuple("Release", [
    "image",
    "config_url",
    "application_name",
    "original_application_name",
    "spinnaker_tags",
    "raw_tags",
    "metadata_annotations"
])

Status = namedtuple("Status", ["status", "info", "logs"])

ApplicationConfiguration = namedtuple("ApplicationConfiguration", [
    "application_data_url",
    "application_name",
    "original_application_name",
    "spinnaker_tags",
    "raw_tags",
    "metadata_annotations"
])
