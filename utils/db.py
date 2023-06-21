import os
from supabase import create_client, Client

from dotenv import load_dotenv
load_dotenv()

url: str = os.environ.get("SUPABASE_URL")
key: str = os.environ.get("SUPABASE_KEY")
supabase: Client = create_client(url, key)
model_table_name = 'models'


def get_model_info(model_id):
    response = supabase.table(model_table_name).select(
        "*").eq("id", model_id).execute()
    if response.data:
        return response.data[0]
    else:
        return None


def update_model_data(model_id: int, data: dict):
    response = supabase.table(model_table_name).update(
        data).eq('id', model_id).execute()
    if response.data:
        return response.data[0]
    else:
        return None


def add_dreambooth_request(images_zip, status, job_id, subject_type, steps,
                           subject_identifier, subject_keyword, title, user_id, base_model_name):
    if base_model_name is None:
        base_model_name = 'runwayml/stable-diffusion-v1-5'
    data = {
        'images_zip': images_zip,
        'status': status,
        'job_id': job_id,
        'subject_type': subject_type,
        'steps': steps,
        'subject_identifier': subject_identifier,
        'subject_keyword': subject_keyword,
        'title': title,
        'user_id': user_id,
        'base_model_name': base_model_name
    },

    response = supabase.table('models').insert(data).execute()
    print(response.data)
    return response.data


# supabase.table('models').update(
#     {'status': "created"}).eq('id', 8).execute()

# Define the values to be inserted
# images_zip = "https://firebasestorage.googleapis.com/v0/b/copykitties-avatar.appspot.com/o/bhumika_aurora.zip?alt=media&token=d0fe3b22-6a59-43e5-ab73-901c60bf0bfe"
# status = "created"
# steps = 1200
# subject_identifier = "6164814fd3264c63a7309a3cee9fb892"
# subject_keyword = "@bhumika"
# subject_type = "person"
# title = "Bhumika"
# base_model_name = "SG161222/Realistic_Vision_V2.0"

# add_dreambooth_request(images_zip=images_zip, status=status, job_id=None, subject_type=subject_type, steps=steps,
#                        subject_identifier=None, subject_keyword=subject_keyword, title=title, user_id="a2c14bd6-f025-4ff0-b98b-18b13ffce6b5", base_model_name=base_model_name)
