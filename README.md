<!--
Copyright 2017-2019 The FIAAS Authors

Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at

     http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.
-->

# MAST

Mast connects Spinnaker to FIAAS.

Receives HTTP requests from Spinnaker for deployments, and creates or updates a FIAAS-app object in the containing
Kubernetes cluster.

Development
-----------

The Development target is Python 3.6.

Install dependencies using `pip`:

    $ pip install -r requirements.txt

Add `bin/format` as a pre-commit step if you want to have your code auto-formatted:

    $ ln -sf ../../bin/format .git/hooks/pre-commit

Optionally, enable auto-formatting on save in Emacs:

    M-x package-install py-yapf

Add the following to `$fiaas-mast/.dir-locals.el`:

    ((python-mode . ((eval . (add-hook 'python-mode-hook 'py-yapf-enable-on-save nil t)))))

Use tox to run tests on multiple python versions:

    $ tox

Tox will use all supported interpreters installed on your system to run tests, but will not complain if an interpreter
is not available.

### IntelliJ runconfigs

#### Running the application

* Create a Python configuration with a suitable name
* Script: Find the `fiaas-mast` executable in the virtualenvs bin directory
    * If using bash, try `which fiaas-mast` inside the virtualenv
* Python Interpreter: Make sure to add the virtualenv as an SDK, and use that interpreter

Set the following env variables to run locally:

```
export ARTIFACTORY_ORIGIN="https://artifactory.yourdomain.com"
export ARTIFACTORY_USER="user.name@schibsted.com"
export ARTIFACTORY_PWD="artifactory-api-key"
export APISERVER_TOKEN="foo"
export APISERVER_CA_CERT="bar"
```

#### Tests

* Create a Python tests -> py.test configuration with a suitable name (name of test-file)
* Target: The specific test-file you wish to run
* Python Interpreter: Make sure to add the virtualenv as an SDK, and use that interpreter

## Release Process

When changes are merged to master the master branch is built
using [semaphore](https://fiaas-svc.semaphoreci.com/projects/mast). The build generates a docker image that is published
to the [fiaas/mast](https://cloud.docker.com/u/fiaas/repository/docker/fiaas/mast) respository on docker hub and is
publicly available. Additionally a helm chart is created and published to
the [fiaas helm repository](https://github.com/fiaas/helm).
