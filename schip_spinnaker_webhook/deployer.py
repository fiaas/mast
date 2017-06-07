import os
import requests


class Deployer:
    def __init__(self, k8s):
        self.k8s = k8s

    def deploy(self, release):
        """Create or update TPR for application"""
        body = """
metadata:
  name: v1beta-example
spec:
  application: v1beta-example
  image: %s
  config:
%s
""" % (release.image, requests.get(release.config_url).text)

        self.k8s.post(
            "/apis/schibsted.io/v1beta/namespaces/{0}/paasbetaapplications/".format(os.environ["NAMESPACE"]),
            body
        )
        return True
