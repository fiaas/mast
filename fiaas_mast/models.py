from collections import namedtuple

Release = namedtuple("Release", [
    "image",
    "config_url",
    "application_name",
    "original_application_name",
    "spinnaker_tags",
    "raw_tags"
])

Status = namedtuple("Status", ["status", "info"])
