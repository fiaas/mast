from .models import Status


def status(application):
    """Get status of a deployment"""
    return Status(status="RUNNING", info="Deployment of {} is still running".format(application))
