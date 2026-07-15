import json
from pydoc_data.topics import topics

from django.dispatch import Signal
from django.dispatch import receiver
from django.db.models.signals import post_save

from backend.apps.shared.repositories.logic import SharedApplicationLogic

object_created = Signal()
object_deleted = Signal()
object_modified = Signal()
object_fetched = Signal()
from backend.apps.common.utils.common_utils import CommonUtils

logger = CommonUtils.get_project_logger(__name__)

shared_logic = SharedApplicationLogic()


@receiver(object_created)
def notify_on_object_created(sender, instance, user, message, **kwargs):
    shared_logic.push_notification_into_kafka(message=json.dumps(message))
