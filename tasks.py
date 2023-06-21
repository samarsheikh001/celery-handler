import os
from time import sleep
import time
from celery import shared_task
from celery.signals import task_success, task_prerun

from utils.db import get_model_info
from utils.redis_helper import get_queue_length
from utils.runpod import find_and_terminate_pod


@shared_task(ignore_result=False, bind=True)
def train_dreambooth(self, user_id: str, model_id: str) -> dict:
    # Add meta data to task
    self.update_state(state='PROGRESS', meta={'current': 0, 'total': 100})
    # Simulating a long running task
    for i in range(5):
        time.sleep(1)
        # Updating meta data during task run
        self.update_state(state='PROGRESS', meta={'current': i, 'total': 100})

    return 2 + 2
    # model_data = get_model_info(model_id)
    # return model_data


@task_success.connect
def task_done_handler(sender=None, **kwargs):
    print(f"Task {sender.name} done!")
    tasks_in_queue = get_queue_length()
    print(f"Tasks in queue: {tasks_in_queue}")
    if tasks_in_queue == 0:
        print("terminate pod")
        find_and_terminate_pod(os.getenv('POD_NAME'))
