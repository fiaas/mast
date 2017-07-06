FROM alpine:3.6
LABEL maintainer="Platform Delivery <platform-delivery@schibsted.com>"

RUN apk add --update ca-certificates git curl tini=0.14.0-r0 py-pip=9.0.1-r1 && \
    mkdir -p /opt/fiaas-mast && \
    adduser -u 10001 -D -h /opt/fiaas-mast fiaas-mast && \
    rm -rf /var/cache/apk/*

EXPOSE 5000

ENTRYPOINT ["/sbin/tini", "--"]

CMD ["fiaas-mast"]

COPY . /opt/fiaas-mast

WORKDIR /opt/fiaas-mast

RUN pip install -r requirements.txt

USER fiaas-mast
