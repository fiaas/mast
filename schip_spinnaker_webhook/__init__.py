import os

from schip_spinnaker_webhook.web import create_app


def main():
    app = create_app()
    app.run(host="0.0.0.0", port=os.getenv('PORT', 5000), debug=os.getenv('DEBUG', False))
