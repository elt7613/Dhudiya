import requests

BASE_URL = 'http://127.0.0.1:8000/api/collector'

token = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ0b2tlbl90eXBlIjoiYWNjZXNzIiwiZXhwIjoxNzQyMDQwMzkxLCJpYXQiOjE3Mzk0NDgzOTEsImp0aSI6IjhkYzFjZDExYzRhNzQ4OTU5MGM3ZmViMjVlZTgxM2NlIiwidXNlcl9pZCI6Mn0.BoL5VCVm903Jq8GYLgz9D8PDOfBZlRtLsRbcVHmZ_z0"

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
    delete_market_milk_price(2)