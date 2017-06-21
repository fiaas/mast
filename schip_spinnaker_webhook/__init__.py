import os

from k8s import config as k8s_config
from schip_spinnaker_webhook.web import create_app


def configure_k8s_client():
    try:
        k8s_config.api_token = os.environ['APISERVER_TOKEN']
    except KeyError:
        token_path = "/var/run/secrets/kubernetes.io/serviceaccount/token"
        if os.path.exists(token_path):
            with open(token_path) as fobj:
                k8s_config.api_token = fobj.read().strip()
        else:
            raise RuntimeError(
                "Could not resolve apiserver token. No $APISERVER_TOKEN set in the environment and "
                "{} did not exist.".format(token_path)
            )

    try:
        k8s_config.verify_ssl = os.environ['APISERVER_CA_CERT']
    except KeyError:
        ca_cert_path = "/var/run/secrets/kubernetes.io/serviceaccount/ca.crt"
        if os.path.exists(ca_cert_path):
            k8s_config.verify_ssl = ca_cert_path
        else:
            raise RuntimeError(
                "Could not resolve apiserver CA certificate. No $APISERVER_CA_CERT set in the "
                "environment and {} did not exist.".format(ca_cert_path)
            )


def main():
    configure_k8s_client()
    app = create_app()
    app.run(host="0.0.0.0", port=int(os.getenv('PORT', 5000)), debug=bool(os.getenv('DEBUG', False)))
