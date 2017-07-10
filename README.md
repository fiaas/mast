FIAAS Mast [![Build Status](https://travis.schibsted.io/spt-infrastructure/fiaas-mast.svg?token=z6c5cx1P1xECeUhxrnJF&branch=master)](https://travis.schibsted.io/spt-infrastructure/fiaas-mast)
==========

<!-- Badger start badges -->
[![Badger](https://badger.spt-engprod-pro.schibsted.io/badge/travis/spt-infrastructure/fiaas-mast)](https://travis.schibsted.io/spt-infrastructure/fiaas-mast) [![Badger](https://badger.spt-engprod-pro.schibsted.io/badge/coverage/spt-infrastructure/fiaas-mast)](https://reports.spt-engprod-pro.schibsted.io/#/spt-infrastructure/fiaas-mast?branch=master&type=push&daterange&daterange) [![Badger](https://badger.spt-engprod-pro.schibsted.io/badge/issues/spt-infrastructure/fiaas-mast)](https://reports.spt-engprod-pro.schibsted.io/#/spt-infrastructure/fiaas-mast?branch=master&type=push&daterange&daterange) [![Badger](https://badger.spt-engprod-pro.schibsted.io/badge/engprod/spt-infrastructure/fiaas-mast)](https://github.schibsted.io/spt-engprod/badger)
<!-- Badger end badges -->

FIAAS Mast connects the Spinnaker to FIAAS.

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


#### Tests

* Create a Python tests -> py.test configuration with a suitable name (name of test-file)
* Target: The specific test-file you wish to run
* Python Interpreter: Make sure to add the virtualenv as an SDK, and use that interpreter
