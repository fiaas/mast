from collections import namedtuple

Release = namedtuple("Release", [
    "image",
    "config_url",
    "application_name",
    "original_application_name",
    "spinnaker_tags",
    "raw_tags",
    "metadata_annotations"
])

Status = namedtuple("Status", ["status", "info", "logs"])

ApplicationConfiguration = namedtuple("ApplicationConfiguration", [
    "application_data_url",
    "application_name",
    "original_application_name",
    "spinnaker_tags",
    "raw_tags",
    "metadata_annotations"
])
