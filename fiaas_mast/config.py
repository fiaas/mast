
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

import os


class Config(object):
    def __init__(self):
        self.PORT = os.environ.get('PORT', 5000)
        self.DEBUG = os.environ.get('DEBUG', False)
        self.APISERVER_TOKEN = self.get_apiserver_token()
        self.APISERVER_CA_CERT = self.get_apiserver_cert()

        self.ARTIFACTORY_USER = os.environ.get('ARTIFACTORY_USER')
        self.ARTIFACTORY_PWD = os.environ.get('ARTIFACTORY_PWD')
        self.ARTIFACTORY_ORIGIN = os.environ.get('ARTIFACTORY_ORIGIN')
        if self.ARTIFACTORY_USER is None or self.ARTIFACTORY_PWD is None or self.ARTIFACTORY_ORIGIN is None:
            raise RuntimeError(
                'You need to pass the \'ARTIFACTORY_USER\', \'ARTIFACTORY_PWD\' and \'ARTIFACTORY_ORIGIN\' '
                'environment variables'
            )
        self.scheme = os.environ.get('URL_SCHEME', 'https')

    def get_apiserver_token(self):
        return os.environ.get('APISERVER_TOKEN')

    def get_apiserver_cert(self):
        return os.environ.get('APISERVER_CA_CERT')
