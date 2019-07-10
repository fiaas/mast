# MAST [![build_status_badge]][build_status] [![codacy_grade_badge]][codacy_grade] [![codacy_coverage_badge]][codacy_coverage]

Mast connects Spinnaker to FIAAS.

[build_status_badge]: https://travis-ci.org/fiaas/mast.svg?branch=master "Build Status"
[build_status]: https://travis-ci.org/fiaas/mast
[codacy_grade_badge]: https://api.codacy.com/project/badge/Grade/59dbd659e01f4e04ad724ae4c8abe2d5 "Codacy Grade"
[codacy_grade]: https://app.codacy.com/app/fiaas/mast?utm_source=github.com&utm_medium=referral&utm_content=fiaas/mast&utm_campaign=badger
[codacy_coverage_badge]: https://api.codacy.com/project/badge/Coverage/59dbd659e01f4e04ad724ae4c8abe2d5 "Codacy Coverage"
[codacy_coverage]: https://www.codacy.com/app/fiaas/mast?utm_source=github.com&utm_medium=referral&utm_content=fiaas/mast&utm_campaign=Badge_Coverage

Receives HTTP requests from Spinnaker for deployments, and creates or updates a FIAAS-app object
in the containing Kubernetes cluster.

Development
-----------

The Development target is Python 3.6.

Install dependencies using `pip`:

    $ pip install -r requirements.txt

Add `bin/format` as a pre-commit step if you want to have your code
auto-formatted:

    $ ln -sf ../../bin/format .git/hooks/pre-commit

Optionally, enable auto-formatting on save in Emacs:

    M-x package-install py-yapf

Add the following to `$fiaas-mast/.dir-locals.el`:

    ((python-mode . ((eval . (add-hook 'python-mode-hook 'py-yapf-enable-on-save nil t)))))

Use tox to run tests on multiple python versions:

    $ tox

Tox will use all supported interpreters installed on your system to run tests, but will not
complain if an interpreter is not available.

### IntelliJ runconfigs

#### Running the application

* Create a Python configuration with a suitable name
* Script: Find the `fiaas-mast` executable in the virtualenvs bin directory
    * If using bash, try `which fiaas-mast` inside the virtualenv
* Python Interpreter: Make sure to add the virtualenv as an SDK, and use that interpreter

Set the following env variables to run locally:
```
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

When changes are merged to master the master branch is built using (travis)[https://travis-ci.org/fiaas/mast]. The build generates a docker image that is published to the (fiaas/mast)[https://cloud.docker.com/u/fiaas/repository/docker/fiaas/mast] respository on docker hub and is publicly available.
Additionally a helm chart is created and published to the (fiaas helm repository)[https://github.com/fiaas/helm].
