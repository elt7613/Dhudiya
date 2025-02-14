import requests

BASE_URL = 'http://127.0.0.1:8000/api/collector'

token = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ0b2tlbl90eXBlIjoiYWNjZXNzIiwiZXhwIjoxNzQyMDUzNzQyLCJpYXQiOjE3Mzk0NjE3NDIsImp0aSI6IjlkNzliOTI1ODAwNDRmM2FhMjlkMGI1NjYyOWE3MzM0IiwidXNlcl9pZCI6Mn0.cC17QJ7Oti-jHw6CfYL_pO-gat4DJJFDrfpurkNOPQ4"

headers = {
    "Authorization": f"Bearer {token}"
}


def create_customer():
    data = {
        "name": "customer 4",
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
    create_customer()