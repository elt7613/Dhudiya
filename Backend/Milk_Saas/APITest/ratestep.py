# Using Python requests
import requests

token = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ0b2tlbl90eXBlIjoiYWNjZXNzIiwiZXhwIjoxNzQyMTE4NDYwLCJpYXQiOjE3Mzk1MjY0NjAsImp0aSI6ImM4NGM4N2FhYzVmZjQ0ZWQ5OGQ4ZWQ0NjJiNjEwOGU0IiwidXNlcl9pZCI6M30.9yAKs1hQlUjjv0Jl4P5SnV4JEgIfJbOxx46NUhjDiIg"

BASE_URL = 'http://127.0.0.1:8000/api/collector'

headers={
    'Authorization': f'Bearer {token}',
    'Content-Type': 'application/json'
}

def get_rate_steps():
    response = requests.get(
        f'{BASE_URL}/rate-steps/',
        headers=headers
    )
    print(response.json())

def get_rate_step(rate_step_id):
    response = requests.get(
        f'{BASE_URL}/rate-steps/{rate_step_id}/',
        headers=headers
    )
    print(response.json())

def create_rate_step():
    data = {
        "rate_type": "rate per kg",
        "milk_type": "cow",
        "fat_from": 4.0,
        "fat_to": 4.5,
        "rate": 50.00
    }

    response = requests.post(
        f'{BASE_URL}/rate-steps/',
        headers=headers,
        json=data
    )
    print(f"Status Code: {response.status_code}")
    print(response.json())
    

def update_rate_step(rate_step_id):
    data = {
        "rate_type": "rate per kg",
        "milk_type": "cow",
        "fat_from": 4.0,
        "fat_to": 4.5,
        "rate": 50.00
    }

    response = requests.put(
        f'{BASE_URL}/rate-steps/{rate_step_id}/',
        headers=headers,
        json=data
    )
    print(response.json())      

def delete_rate_step(rate_step_id):
    response = requests.delete(
        f'{BASE_URL}/rate-steps/{rate_step_id}/',
        headers=headers
    )
    print(response.status_code)
    print(response.json())


if __name__ == "__main__":
    create_rate_step() 