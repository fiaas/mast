
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
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

from datetime import datetime
from subprocess import check_output, CalledProcessError

from setuptools import setup, find_packages
from warnings import warn


def version():
    date_string = datetime.now().strftime("1.%Y%m%d.%H%M%S")
    try:
        git_sha = check_output(["git", "describe", "--always", "--dirty=dirty", "--match=NOTHING"]).strip().decode()
        return "{}+{}".format(date_string, git_sha)
    except CalledProcessError as e:
        warn("Error calling git: {}".format(e))
    return date_string


GEN_REQ = [
    "Flask==1.1.1",
    "flask-talisman==0.7.0",
    "flask-bootstrap==3.3.7.1",
    "PyYAML==5.1.2",
    "requests==2.22.0",
    "six==1.12.0",
    "ipaddress==1.0.22",
    "k8s==0.13.0",
    "prometheus_client == 0.7.1",
]

CODE_QUALITY_REQ = [
    "prospector==1.7.7",
]

CI_REQ = [
    "tox==3.13.2",
    "tox-travis==0.12",
]

TEST_REQ = [
    'mock==3.0.5',
    'pytest-sugar==0.9.2',
    'pytest==3.10.1',
    "pytest-cov==2.7.1",
    "pytest-html==1.22.0",
]

setup(
    name="fiaas-mast",
    url="https://github.com/fiaas/mast",
    maintainer="fiaas",
    maintainer_email="fiaas@googlegroups.com",
    version=version(),
    packages=find_packages(),
    include_package_data=True,
    install_requires=GEN_REQ,
    extras_require={
        "dev": ['yapf==0.16.1'] + TEST_REQ + CODE_QUALITY_REQ + CI_REQ,
        "ci": CI_REQ,
        "codacy": ["codacy-coverage"]
    },
    setup_requires=['setuptools>=17.1', 'pytest-runner', 'wheel'],
    entry_points={"console_scripts": ['fiaas-mast=fiaas_mast.__main__:main']},
)
