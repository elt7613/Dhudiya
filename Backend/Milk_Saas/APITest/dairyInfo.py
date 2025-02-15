import requests

BASE_URL = 'http://127.0.0.1:8000/api/collector'

token = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ0b2tlbl90eXBlIjoiYWNjZXNzIiwiZXhwIjoxNzQyMTE4NDYwLCJpYXQiOjE3Mzk1MjY0NjAsImp0aSI6ImM4NGM4N2FhYzVmZjQ0ZWQ5OGQ4ZWQ0NjJiNjEwOGU0IiwidXNlcl9pZCI6M30.9yAKs1hQlUjjv0Jl4P5SnV4JEgIfJbOxx46NUhjDiIg"

headers = {
    "Authorization": f"Bearer {token}"
}

def create_dairy_info():
    data = {
        "dairy_name": "Dairy 1",
        "dairy_address": "123 Main St, Anytown, USA",
        "rate_type": "fat_snf"
    }
    response = requests.post(f"{BASE_URL}/dairy-information/", json=data, headers=headers)
    print(response.json())

if __name__ == "__main__":
    create_dairy_info()