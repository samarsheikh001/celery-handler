import logging
import os
from time import sleep
from celery import shared_task
from celery.signals import task_success, task_prerun
from model_training import cleanup, prepare_model, train_model

from utils.db import get_model_info, update_model_data
from utils.redis_helper import get_queue_length
from utils.runpod import find_and_terminate_pod

logger = logging.getLogger(__name__)


# @shared_task(ignore_result=False, bind=True)
# def train_dreambooth(self, user_id: str, model_id: str) -> dict:
#     try:
#         model_data = get_model_info(model_id)
#         steps = model_data["steps"]
#         subjectType = model_data["subject_type"]
#         images_zip = model_data["images_zip"]
#         base_model_name = model_data["base_model_name"]
#         instance_prompt = "a photo of a person" if subjectType == "person" else "Unknown subject type"
#         subjectIdentifier = generate_identifier()
#         job_id = self.request.id
#         update_model_data(
#             model_id, {'status': "training_started", "subject_identifier": subjectIdentifier, "job_id": job_id})
#         # Download and extract images
#         if images_zip:
#             download_and_extract_zip(images_zip, extract_to=subjectIdentifier)
#         # # Add meta data to task
#         # self.update_state(state='PROGRESS', meta={'current': 0, 'total': 100})
#         # Prepare the command
#         cmd = [
#             "accelerate",
#             "launch",
#             "train_dreambooth.py",
#             "--pretrained_model_name_or_path", base_model_name,
#             "--instance_data_dir", subjectIdentifier,
#             "--output_dir", "output",
#             "--instance_prompt", f"{instance_prompt} {subjectIdentifier}",
#             "--resolution", "512",
#             "--train_batch_size", "1",
#             "--gradient_accumulation_steps", "1",
#             "--learning_rate", "2e-6",
#             "--lr_scheduler", "constant",
#             "--lr_warmup_steps", "0",
#             "--max_train_steps", str(steps),
#         ]

#         # Run the command
#         subprocess.run(cmd)
#         convert_model(f"output/{steps}", f"{subjectIdentifier}.ckpt", True)
#         upload_file_to_s3(f"{subjectIdentifier}.ckpt",
#                           f"{subjectIdentifier}.ckpt")
#         # Clean up storage
#         delete_file_or_folder(subjectIdentifier)  # Delete images folder
#         delete_file_or_folder("output")
#         delete_file_or_folder(f"{subjectIdentifier}.ckpt")

#         update_model_data(
#             model_id, {'status': "finished"})
#         return model_data
#     except Exception as e:
#         print(f"Error encountered: {e}")
#         # Update the request status to 'FAILED'
#         update_model_data(
#             model_id, {'status': "error"})
#         # Rethrow the exception if you want to handle it further up in the call stack
#         raise

@shared_task(ignore_result=False, bind=True)
def train_dreambooth(self, user_id: str, model_id: str) -> dict:
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


# train_dreambooth("sdaasd", 15)
