import requests

BASE_URL = 'http://127.0.0.1:8000/api/collector'


token = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ0b2tlbl90eXBlIjoiYWNjZXNzIiwiZXhwIjoxNzQyMzg5MTIyLCJpYXQiOjE3Mzk3OTcxMjIsImp0aSI6IjY4Zjg1ZTQ1ZTUyMTRkYjU5ZjZlMGM5M2Q2MWRmNzMwIiwidXNlcl9pZCI6Mn0.tDW4q6MiVkjqUXf8ltKl7TS0mnIjDyTV0R7LHnMFZ0Q"

headers = {
    "Authorization": f"Bearer {token}"
}

def create_dairy_info():
    data = {
        "dairy_name": "Kun dairy Milk",
        "dairy_address": "123 Main St, Anytown, USA",
        "rate_type": "fat_snf"
    }
    response = requests.post(f"{BASE_URL}/dairy-information/", json=data, headers=headers)
    print(response.json())

def get_dairy_info():
    response = requests.get(f"{BASE_URL}/dairy-information/", headers=headers)
    print(response.json())

def update_dairy_info(dairy_id):
    data = {
        "dairy_name": "Kun  Milk",
        "dairy_address": "123 Main St, Anytown, USA",
        "rate_type": "fat_snf"
    }
    response = requests.put(f"{BASE_URL}/dairy-information/{dairy_id}/", json=data, headers=headers)
    print(response.json())

if __name__ == "__main__":
    update_dairy_info(1)