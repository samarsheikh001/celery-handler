import os
import uuid
import requests

from dotenv import load_dotenv
load_dotenv()

API_KEY = os.getenv("RUNPOD_API_KEY")

# GraphQL API endpoint URL
url = f"https://api.runpod.io/graphql?api_key={API_KEY}"

# GraphQL request headers
headers = {
    "Content-Type": "application/json",
}


def generate_uuid():
    return str(uuid.uuid4())


def fetch_minimum_bid_price(gpu_id):
    # Example query
    query = '''
        query GpuTypes($gpuId: String!) {
          gpuTypes(input: {id: $gpuId}) {
            id
            displayName
            memoryInGb
            secureCloud
            communityCloud
            lowestPrice(input: {gpuCount: 1}) {
              minimumBidPrice
              uninterruptablePrice
            }
          }
        }
    '''
    payload = {
        "query": query,
        "variables": {
            "gpuId": gpu_id
        }
    }

    response = requests.post(url, headers=headers, json=payload)

    if response.status_code == 200:
        data = response.json()
        gpu_types = data["data"]["gpuTypes"]
        return gpu_types[0]['lowestPrice']['minimumBidPrice']
    else:
        print("GraphQL request failed with status code:", response.status_code)
        print(response.text)
        return None


def query_gpu_types():
    data = {
        'query': '''
            query GpuTypes {
              gpuTypes {
                id
                displayName
                memoryInGb
              }
            }
        '''
    }

    response = requests.post(url, headers=headers, json=data)

    if response.status_code == 200:
        result = response.json()
        gpu_types = result['data']['gpuTypes']
        for gpu in gpu_types:
            print(f"GPU ID: {gpu['id']}")
            print(f"Display Name: {gpu['displayName']}")
            print(f"Memory: {gpu['memoryInGb']} GB")
            print()  # Empty line for separation
        return result  # Return the result or process it further as needed
    else:
        print('Request failed with status code:', response.status_code)
        return None  # Return None or handle the error case accordingly


def rent_pod(gpu_id, minimum_bid_price):
    identifier = generate_uuid()
    query = f"""
  mutation RentPod($gpuId: String!, $minimumBidPrice: Float!) {{
    podRentInterruptable(
     input: {{
      bidPerGpu: $minimumBidPrice
      cloudType: COMMUNITY
      gpuCount: 1
      minDownload: 300
      minUpload: 100
      volumeInGb: 40
      containerDiskInGb: 40
      minVcpuCount: 2
      minMemoryInGb: 15
      gpuTypeId: $gpuId
      name: "{identifier}"
      imageName: "getrektx/dreambooth-server:latest"
      dockerArgs: ""
      ports: ""
      volumeMountPath: "/workspace"
      env: [
        {{ key: "S3_ENDPOINT_URL", value: "{os.getenv("S3_ENDPOINT_UR")}" }},
        {{ key: "S3_ACCESS_KEY_ID", value: "{os.getenv("S3_ACCESS_KEY_ID")}" }},
        {{ key: "S3_SECRET_ACCESS_KEY", value: "{os.getenv("S3_SECRET_ACCESS_KEY")}" }},
        {{ key: "HUGGINGFACE_TOKEN", value: "{os.getenv("HUGGINGFACE_TOKEN")}" }},
        {{ key: "POD_NAME", value: "{identifier}" }},
        {{ key: "RUNPOD_API_KEY", value: "{os.getenv("RUNPOD_API_KEY")}" }},
      ]
    }}
  ) {{
    id
    imageName
    env
    machineId
    machine {{
      podHostId
    }}
  }}
}}
"""
    payload = {
        "query": query,
        "variables": {
            "gpuId": gpu_id,
            "minimumBidPrice": minimum_bid_price
        }
    }

    response = requests.post(url, headers=headers, json=payload)

    if response.status_code == 200:
        data = response.json()
        print(data)
        rented_pod = data["data"]["podRentInterruptable"]
        return identifier
    else:
        print("GraphQL request failed with status code:", response.status_code)
        print(response.text)
        return None


def stop_pod(pod_id):
    query = '''
        mutation StopPod($podId: String!) {
          podStop(input: {podId: $podId}) {
            id
            desiredStatus
          }
        }
    '''
    payload = {
        "query": query,
        "variables": {
            "podId": pod_id
        }
    }

    response = requests.post(url, headers=headers, json=payload)

    if response.status_code == 200:
        data = response.json()
        stopped_pod = data["data"]["podStop"]
        return stopped_pod
    else:
        print("GraphQL request failed with status code:", response.status_code)
        print(response.text)
        return None


def terminate_pod(pod_id):
    query = '''
        mutation PodTerminate($input: PodTerminateInput!) {
          podTerminate(input: $input)
        }
    '''
    payload = {
        "query": query,
        "variables": {
            "input": {
                "podId": pod_id
            }
        }
    }

    response = requests.post(url, headers=headers, json=payload)

    if response.status_code == 200:
        data = response.json()
        return data
    else:
        print("GraphQL request failed with status code:", response.status_code)
        print(response.text)
        return None


def get_pods():
    query = '''
        query Pods {
          myself {
            pods {
              id
              name
              runtime {
                uptimeInSeconds
                ports {
                  ip
                  isIpPublic
                  privatePort
                  publicPort
                  type
                }
                gpus {
                  id
                  gpuUtilPercent
                  memoryUtilPercent
                }
                container {
                  cpuPercent
                  memoryPercent
                }
              }
            }
          }
        }
    '''
    payload = {
        "query": query,
    }

    response = requests.post(url, headers=headers, json=payload)

    if response.status_code == 200:
        data = response.json()
        pods = data["data"]["myself"]["pods"]
        return pods
    else:
        print("GraphQL request failed with status code:", response.status_code)
        print(response.text)
        return None


def find_and_terminate_pod(name_to_find):
    pods = get_pods()
    found_id = None

    for item in pods:
        if item['name'] == name_to_find:
            found_id = item['id']
            terminate_pod(found_id)
            break


def query_pod(pod_id):
    # GraphQL query
    query = '''
    query Pod {
      pod(input: {podId: "%s"}) {
        id
        name
        runtime {
          uptimeInSeconds
          ports {
            ip
            isIpPublic
            privatePort
            publicPort
            type
          }
          gpus {
            id
            gpuUtilPercent
            memoryUtilPercent
          }
          container {
            cpuPercent
            memoryPercent
          }
        }
      }
    }
    ''' % pod_id

    # GraphQL request
    response = requests.post(url, json={'query': query})

    if response.status_code == 200:
        data = response.json()
        return data['data']['pod']
    else:
        print('Error:', response.status_code)
        return None


# # Usage
# pod_info = query_pod('4xegomyegaqzsu')
# if pod_info:
#     print(pod_info)

# min_bid_price = fetch_minimum_bid_price("NVIDIA GeForce RTX 4090")
# rent_pod("NVIDIA GeForce RTX 4090", min_bid_price+0.01)

# print(query_gpu_types())
