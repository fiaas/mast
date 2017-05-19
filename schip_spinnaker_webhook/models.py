from collections import namedtuple

Deployment = namedtuple("Deployment", ["image", "config_url"])

Status = namedtuple("Status", ["status", "info"])
