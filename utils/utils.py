import io
import os
import shutil
import uuid
import zipfile

import requests


def delete_file_or_folder(path):
    if os.path.isfile(path):
        os.remove(path)  # remove the file
    elif os.path.isdir(path):
        shutil.rmtree(path)  # remove dir and all contains


def generate_identifier():
    identifier = str(uuid.uuid4()).replace("-", "")
    return identifier


def download_and_extract_zip(url, extract_to='.'):
    print(f"Downloading and extracting zip file from {url}")
    response = requests.get(url)
    with zipfile.ZipFile(io.BytesIO(response.content)) as zip_file:
        zip_file.extractall(path=extract_to)
