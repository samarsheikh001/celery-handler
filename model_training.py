import subprocess
from utils.db import update_model_data
from utils.to_ckpt import convert_model
from utils.upload import upload_file_to_s3
from utils.utils import delete_file_or_folder, download_and_extract_zip, generate_identifier


def prepare_model(model_data: dict, model_id: str, job_id: str) -> str:
    subject_type = model_data["subject_type"]
    instance_prompt = "a photo of a person" if subject_type == "person" else "Unknown subject type"
    subject_identifier = generate_identifier()
    model_data = update_model_data(
        model_id, {'status': "training_started", "subject_identifier": subject_identifier, "job_id": job_id})
    if model_data["images_zip"]:
        download_and_extract_zip(
            model_data["images_zip"], extract_to=subject_identifier)
    return subject_identifier, instance_prompt


def train_model(base_model_name: str, subject_identifier: str, instance_prompt: str, steps: int):
    cmd = [
        "accelerate",
        "launch",
        "train_dreambooth.py",
        "--pretrained_model_name_or_path", base_model_name,
        "--instance_data_dir", subject_identifier,
        "--output_dir", "output",
        "--instance_prompt", f"{instance_prompt} {subject_identifier}",
        "--resolution", "512",
        "--train_batch_size", "1",
        "--gradient_accumulation_steps", "1",
        "--learning_rate", "2e-6",
        "--lr_scheduler", "constant",
        "--lr_warmup_steps", "0",
        "--max_train_steps", str(steps),
    ]
    subprocess.run(cmd)


def cleanup(subject_identifier: str, steps: int):
    convert_model(f"output/{steps}", f"{subject_identifier}.ckpt", True)
    upload_file_to_s3(f"{subject_identifier}.ckpt",
                      f"{subject_identifier}.ckpt")
    delete_file_or_folder(subject_identifier)  # Delete images folder
    delete_file_or_folder("output")
    delete_file_or_folder(f"{subject_identifier}.ckpt")
