import logging
import os
from time import sleep
from celery import shared_task
from celery.signals import task_success, task_prerun, worker_process_init
from model_training import cleanup, prepare_model, train_model

from utils.db import get_model_info, update_model_data
from utils.redis_helper import get_queue_length
from utils.runpod import find_and_terminate_pod

logger = logging.getLogger(__name__)


@shared_task(ignore_result=False, bind=True)
def train_dreambooth(self, model_id: str) -> dict:
    model_data = get_model_info(model_id)
    steps = model_data["steps"]
    base_model_name = model_data["base_model_name"]
    job_id = self.request.id
    try:
        subject_identifier, instance_prompt = prepare_model(
            model_data, model_id, job_id)
        train_model(base_model_name, subject_identifier,
                    instance_prompt, steps)
        cleanup(subject_identifier, steps)
        update_model_data(model_id, {'status': "finished"})
        return model_data

    except Exception as e:
        logger.error(f"Error encountered: {e}")
        update_model_data(model_id, {'status': "error"})
        raise


@task_success.connect
def task_done_handler(sender=None, **kwargs):
    print(f"Task {sender.name} done!")
    tasks_in_queue = get_queue_length()
    print(f"Tasks in queue: {tasks_in_queue}")
    if tasks_in_queue == 0:
        print("terminate pod")
        find_and_terminate_pod(os.getenv('POD_NAME'))


@worker_process_init.connect
def setup_worker_init(sender=None, conf=None, **kwargs):
    print("Worker initialised")
    tasks_in_queue = get_queue_length()
    print(f"Tasks in queue: {tasks_in_queue}")
    if tasks_in_queue == 0:
        print("terminate pod")
        find_and_terminate_pod(os.getenv('POD_NAME'))


train_dreambooth(15)
