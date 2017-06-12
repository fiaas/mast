import os

from schip_spinnaker_webhook.web import create_app


def main():
    app = create_app()
    app.run(host="0.0.0.0", port=int(os.getenv('PORT', 5000)), debug=bool(os.getenv('DEBUG', False)))
