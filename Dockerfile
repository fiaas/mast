FROM alpine:3.6
LABEL maintainer="Platform Delivery <platform-delivery@schibsted.com>"

ENV CONTAINER_PORT 5000

HEALTHCHECK --interval=10s --timeout=2s --retries=3 \
      CMD curl -f http://localhost:${CONTAINER_PORT}/health || exit 1

COPY . /opt/schip-spinnaker-webhook

RUN apk add --update git curl tini=0.14.0-r0 py-pip=9.0.1-r1 && \
    adduser -u 10001 -D -h /opt/schip-spinnaker-webhook schip-spinnaker-webhook && \
    rm -rf /var/cache/apk/*

WORKDIR /opt/schip-spinnaker-webhook

RUN pip install -r requirements.txt

EXPOSE ${CONTAINER_PORT}

ENTRYPOINT ["/sbin/tini", "--"]

CMD ["schip-spinnaker-webhook"]

USER schip-spinnaker-webhook
