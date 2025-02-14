import requests
from datetime import date

BASE_URL = 'http://127.0.0.1:8000/api/collector'

token = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ0b2tlbl90eXBlIjoiYWNjZXNzIiwiZXhwIjoxNzQyMDQwMzkxLCJpYXQiOjE3Mzk0NDgzOTEsImp0aSI6IjhkYzFjZDExYzRhNzQ4OTU5MGM3ZmViMjVlZTgxM2NlIiwidXNlcl9pZCI6Mn0.BoL5VCVm903Jq8GYLgz9D8PDOfBZlRtLsRbcVHmZ_z0"

headers = {
    "Authorization": f"Bearer {token}"
}


def create_collection(customer_id):
    data = {
            "collection_time": "morning",
            "milk_type": "buffalo",
            "customer": customer_id,
            "collection_date": str(date.today()),
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
        "collection_date": str(date.today()),
        "measured": "kg",
        "liters": "12.0",
        "kg": "12.0",
        "fat_percentage": "3.8",
        "fat_kg": "12.0",
        "clr": "6.5",
        "snf_percentage": "7.5",
        "snf_kg": "12.0",
        "fat_rate": "42.00",
        "snf_rate": "42.00",
        "rate": "100.50",
        "amount": "42.00"
    }
    response = requests.put(f'{BASE_URL}/collections/{collection_id}/', json=data, headers=headers)
    print(response.json())



def delete_collection(collection_id):
    response = requests.delete(f'{BASE_URL}/collections/{collection_id}/', headers=headers)
    print(response.json())

if __name__ == "__main__":
    create_collection(1)


