import requests
from datetime import date

BASE_URL = 'http://127.0.0.1:8000/api/collector'

token = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ0b2tlbl90eXBlIjoiYWNjZXNzIiwiZXhwIjoxNzQyNDY1NDIzLCJpYXQiOjE3Mzk4NzM0MjMsImp0aSI6ImY4NTAzZjQwMTdiNTQ2NTU5ZmViNjVjYTYzMzZiYWYxIiwidXNlcl9pZCI6Nn0.2dJjMBTyCX4DwA5n9Qdep-T5i5MxyzJa3ZU6qgWC9Yc"

headers = {
    "Authorization": f"Bearer {token}"
}

def create_collection(customer_id):
    data = {
            "collection_time": "morning",
            "milk_type": "mix",
            "customer": customer_id,
            "collection_date": '2025-02-21',
            "measured": "liters",
            "liters": "10.5",
            "kg": "10.5",
            "fat_percentage": "5.2",
            "fat_kg": "10.5",
            "clr": "6.5",
            "snf_percentage": "6.5",
            "snf_kg": "10.5",
            "fat_rate": "475.50",
            "snf_rate": "475.50",
            "rate": "100.50",
            "base_snf_percentage": "9.2",
            "amount": "475.50"
        }
    
    response = requests.post(f'{BASE_URL}/collections/', json=data, headers=headers)
    print(response.json())


def get_collections():
    response = requests.get(f'{BASE_URL}/collections/', headers=headers)
    print(response.json())


def get_collection(collection_id):
    response = requests.get(f'{BASE_URL}/collections/{collection_id}/', headers=headers)
    print(response.json())

    
def update_collection(collection_id,customer_id):
    data = {
            "collection_time": "evening",
            "milk_type": "cow",
            "customer": customer_id,
            "collection_date": '2025-02-21',
            "measured": "liters",
            "liters": "10.5",
            "kg": "10.5",
            "fat_percentage": "5.2",
            "fat_kg": "10.5",
            "clr": "6.5",
            "snf_percentage": "6.5",
            "snf_kg": "10.5",
            "fat_rate": "475.50",
            "snf_rate": "475.50",
            "rate": "100.50",
            #"base_snf_percentage": "9.4",
            "amount": "475.50"
        }
    response = requests.put(f'{BASE_URL}/collections/{collection_id}/', json=data, headers=headers)
    print(response.json())



def delete_collection(collection_id):
    response = requests.delete(f'{BASE_URL}/collections/{collection_id}/', headers=headers)
    print(response.status_code)

if __name__ == "__main__":
    create_collection(1)


