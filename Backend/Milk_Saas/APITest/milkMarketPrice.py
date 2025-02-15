import requests

BASE_URL = 'http://127.0.0.1:8000/api/collector'

token = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ0b2tlbl90eXBlIjoiYWNjZXNzIiwiZXhwIjoxNzQyMTE4NDYwLCJpYXQiOjE3Mzk1MjY0NjAsImp0aSI6ImM4NGM4N2FhYzVmZjQ0ZWQ5OGQ4ZWQ0NjJiNjEwOGU0IiwidXNlcl9pZCI6M30.9yAKs1hQlUjjv0Jl4P5SnV4JEgIfJbOxx46NUhjDiIg"

headers = {
    "Authorization": f"Bearer {token}"
}

def get_market_milk_prices():
    response = requests.get(f'{BASE_URL}/market-milk-prices/', headers=headers)
    print(response.json())

def get_market_milk_price(price_id):
    response = requests.get(f'{BASE_URL}/market-milk-prices/{price_id}/', headers=headers)
    print(response.json())

def create_market_milk_price():
    data = {
        "price": 200
    }
    response = requests.post(f'{BASE_URL}/market-milk-prices/', headers=headers, json=data)
    print(response.json())


def update_market_milk_price(price_id):
    data = {
        "price": 50
    }
    response = requests.put(f'{BASE_URL}/market-milk-prices/{price_id}/', headers=headers, json=data)
    print(response.json())

def delete_market_milk_price(price_id):
    response = requests.delete(f'{BASE_URL}/market-milk-prices/{price_id}/', headers=headers)
    print(response.status_code)



if __name__ == "__main__":
    create_market_milk_price()