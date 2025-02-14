# Using Python requests
import requests

token = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ0b2tlbl90eXBlIjoiYWNjZXNzIiwiZXhwIjoxNzQyMDQwMzkxLCJpYXQiOjE3Mzk0NDgzOTEsImp0aSI6IjhkYzFjZDExYzRhNzQ4OTU5MGM3ZmViMjVlZTgxM2NlIiwidXNlcl9pZCI6Mn0.BoL5VCVm903Jq8GYLgz9D8PDOfBZlRtLsRbcVHmZ_z0"

BASE_URL = 'http://127.0.0.1:8000/api/collector'

headers={
    'Authorization': f'Bearer {token}',
    'Content-Type': 'application/json'
}

def get_rate_charts():
# Get all rate charts
    response = requests.get(
        f'{BASE_URL}/rate-charts/',
        headers=headers
    )
    print(response.json())

# Get specific rate chart by ID
def get_rate_chart(rate_chart_id):
    response = requests.get(
        f'{BASE_URL}/rate-charts/{rate_chart_id}/',
        headers=headers
    )
    print(response.json())

def create_rate_chart():
    data = {
    "rate_type": "rate per kg",
    "milk_type": "buffalo",
    "fat_from": 4.0,
    "fat_to": 4.5,
    "rate": 50.00
    }

    response = requests.post(
        f'{BASE_URL}/rate-charts/',
        headers=headers,
        json=data
    )
    print(f"Status Code: {response.status_code}")
    print(response.json())
    

def update_rate_chart(rate_chart_id):
    data = {
        "rate_type": "rate per kg",
        "milk_type": "cow",
        "fat_from": 4.0,
        "fat_to": 4.5,
        "rate": 50.00
    }

    response = requests.put(
        f'{BASE_URL}/rate-charts/{rate_chart_id}/',
        headers=headers,
        json=data
    )
    print(response.json())      

def delete_rate_chart(rate_chart_id):
    response = requests.delete(
        f'{BASE_URL}/rate-charts/{rate_chart_id}/',
        headers=headers
    )
    print(response.status_code)
    print(response.json())


if __name__ == "__main__":
    delete_rate_chart(3)