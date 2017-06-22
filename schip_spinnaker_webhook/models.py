from collections import namedtuple

Release = namedtuple("Release", ["image", "config_url", "application_name"])

Status = namedtuple("Status", ["status", "info"])
