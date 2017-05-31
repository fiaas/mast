import os
import urllib


class Deployer:
    def __init__(self, k8s):
        self.k8s = k8s

    def deploy(self, deployment):
        """Create or update TPR for application"""
        body = """
apiVersion: "schibsted.io/v1beta"
kind: PaasbetaApplication
metadata:
  name: v1beta-example
spec:
  application: v1beta-example
  image: %s
  config:
%s
""" % (deployment.image, urllib.request.urlopen(deployment.config_url).read())

        self.k8s.post(
            "/apis/schibsted.io/v1beta/namespaces/{0}/paasbetaapplications/".format(self._get_namespace()),
            body
        )
        return True

    def _get_namespace(self):
        """Namespace for the TPR. The namespace for this webhook will be used unless an ENV variable is passed"""
        if "NAMESPACE" in os.environ:
            namespace = os.environ["NAMESPACE"]
        else:
            with open("/var/run/secrets/kubernetes.io/serviceaccount/namespace") as f:
                namespace = f.read()

        return namespace
