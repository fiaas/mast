FROM alpine:3.6
LABEL maintainer="Platform Delivery <platform-delivery@schibsted.com>"

RUN apk add --update git curl tini=0.14.0-r0 py-pip=9.0.1-r1 && \
    mkdir -p /opt/schip-spinnaker-webhook && \
    adduser -u 10001 -D -h /opt/schip-spinnaker-webhook schip-spinnaker-webhook && \
    rm -rf /var/cache/apk/*

EXPOSE 5000

ENTRYPOINT ["/sbin/tini", "--"]

CMD ["schip-spinnaker-webhook"]

COPY . /opt/schip-spinnaker-webhook

WORKDIR /opt/schip-spinnaker-webhook

RUN pip install -r requirements.txt

USER schip-spinnaker-webhook
