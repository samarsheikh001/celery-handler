import os
from supabase import create_client, Client

from dotenv import load_dotenv
load_dotenv()

url: str = os.environ.get("SUPABASE_URL")
key: str = os.environ.get("SUPABASE_KEY")
supabase: Client = create_client(url, key)


def get_model_info(model_id):
    response = supabase.table('models').select(
        "*").eq("id", model_id).execute()
    if response.data:
        return response.data[0]
    else:
        return None


def add_dreambooth_request(images_zip, status, job_id, subjectType, steps,
                           subjectIdentifier, subjectKeyword, title, user_id):
    data = {
        'images_zip': images_zip,
        'status': status,
        'job_id': job_id,
        'subjectType': subjectType,
        'steps': steps,
        'subjectIdentifier': subjectIdentifier,
        'subjectKeyword': subjectKeyword,
        'title': title,
        'user_id': user_id
    },

    response = supabase.table('models').insert(data).execute()
    print(response.data)
    return response.data


# # Define the values to be inserted
# images_zip = "https://firebasestorage.googleapis.com/v0/b/copykitties-avatar.appspot.com/o/bhumika_aurora.zip?alt=media&token=d0fe3b22-6a59-43e5-ab73-901c60bf0bfe"
# status = "created"
# steps = 1200
# subjectIdentifier = "6164814fd3264c63a7309a3cee9fb892"
# subjectKeyword = "@bhumika"
# subjectType = "person"
# title = "Bhumika"

# add_dreambooth_request(images_zip=images_zip, status=status, job_id=None, subjectType=subjectType, steps=steps,
#                        subjectIdentifier=None, subjectKeyword=subjectKeyword, title=title, user_id="a2c14bd6-f025-4ff0-b98b-18b13ffce6b5")
