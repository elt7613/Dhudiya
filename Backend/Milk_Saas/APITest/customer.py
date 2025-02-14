import requests

BASE_URL = 'http://127.0.0.1:8000/api/collector'

token = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ0b2tlbl90eXBlIjoiYWNjZXNzIiwiZXhwIjoxNzQyMTE4NDYwLCJpYXQiOjE3Mzk1MjY0NjAsImp0aSI6ImM4NGM4N2FhYzVmZjQ0ZWQ5OGQ4ZWQ0NjJiNjEwOGU0IiwidXNlcl9pZCI6M30.9yAKs1hQlUjjv0Jl4P5SnV4JEgIfJbOxx46NUhjDiIg"

headers = {
    "Authorization": f"Bearer {token}"
}

def create_customer():
    data = {
        "name": "customer 8",
        "phone": "+919876543210"
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
        "name": "customer 1 updated",
        "phone": "+919876543210"
    }
    response = requests.put(f'{BASE_URL}/customers/{customer_id}/', json=data, headers=headers)
    print(response.json())


def delete_customer(customer_id):
    response = requests.delete(f'{BASE_URL}/customers/{customer_id}/', headers=headers)
    print("Delete Customer Response:", response.status_code)
    print(response.json())
    
if __name__ == "__main__":
    get_customers()