import requests

BASE_URL = 'http://127.0.0.1:8000/api/collector'

token = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ0b2tlbl90eXBlIjoiYWNjZXNzIiwiZXhwIjoxNzQyMzg5MTIyLCJpYXQiOjE3Mzk3OTcxMjIsImp0aSI6IjY4Zjg1ZTQ1ZTUyMTRkYjU5ZjZlMGM5M2Q2MWRmNzMwIiwidXNlcl9pZCI6Mn0.tDW4q6MiVkjqUXf8ltKl7TS0mnIjDyTV0R7LHnMFZ0Q"

headers = {
    "Authorization": f"Bearer {token}"
}

def create_customer():
    data = {
        "name": "new customer",
        "phone": "9276543210"
    }

    response = requests.post(f'{BASE_URL}/customers/', json=data, headers=headers)

    print(response.json())


def get_customers():
    response = requests.get(f'{BASE_URL}/customers/?page=1', headers=headers)
    print(response.json())


def get_customer(customer_id):
    response = requests.get(f'{BASE_URL}/customers/{customer_id}/', headers=headers)
    print(response.json())


def update_customer(customer_id):
    data = {
        "name": "test customer 22",
        "phone": "9876543210"
    }
    response = requests.put(f'{BASE_URL}/customers/{customer_id}/', json=data, headers=headers)
    print(response.json())


def delete_customer(customer_id):
    response = requests.delete(f'{BASE_URL}/customers/{customer_id}/', headers=headers)
    print("Delete Customer Response:", response.status_code)
    print(response.status_code)
    
if __name__ == "__main__":
    create_customer()