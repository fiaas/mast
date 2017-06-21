import os

from k8s import config as k8s_config
from schip_spinnaker_webhook.web import create_app

def configure_k8s_client():
    token_path = "/var/run/secrets/kubernetes.io/serviceaccount/token"
    if os.path.exists(token_path):
        with open(token_path) as fobj:
            k8s_config.api_token = fobj.read().strip()

    ca_cert_path = "/var/run/secrets/kubernetes.io/serviceaccount/ca.crt"
    if os.path.exists(token_file):
        k8s_config.verify_ssl = ca_cert_file

def main():
    configure_k8s_client()
    app = create_app()
    app.run(host="0.0.0.0", port=int(os.getenv('PORT', 5000)), debug=bool(os.getenv('DEBUG', False)))
