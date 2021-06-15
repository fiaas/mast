
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

FROM python:3.6-alpine3.7 as common
LABEL maintainer="fiaas <fiaas@googlegroups.com>"

RUN apk --no-cache add --update ca-certificates tini=0.16.1-r0 yaml && \
    mkdir -p /opt/fiaas-mast && \
    adduser -u 10001 -D -h /opt/fiaas-mast fiaas-mast

FROM common as build
# Install build tools, and build wheels of all dependencies
RUN apk --no-cache add \
    build-base \
    git \
    curl \
    yaml-dev
COPY . /opt/fiaas-mast
COPY .wheel_cache/*.whl /links/
WORKDIR /opt/fiaas-mast
RUN pip wheel . --quiet --no-cache-dir --wheel-dir=/wheels/ --find-links=/links/

FROM common as production
# Get rid of all build dependencies, install application using only pre-built binary wheels
COPY --from=build /wheels/ /wheels/
RUN pip install --quiet --no-index --no-cache-dir --find-links=/wheels/ --only-binary all /wheels/fiaas_mast*.whl
USER fiaas-mast
EXPOSE 5000
ENTRYPOINT ["/sbin/tini", "--"]
CMD ["fiaas-mast"]
