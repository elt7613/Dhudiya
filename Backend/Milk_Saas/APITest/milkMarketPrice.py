import requests

BASE_URL = 'http://127.0.0.1:8000/api/collector'

token = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ0b2tlbl90eXBlIjoiYWNjZXNzIiwiZXhwIjoxNzQyMzg5MTIyLCJpYXQiOjE3Mzk3OTcxMjIsImp0aSI6IjY4Zjg1ZTQ1ZTUyMTRkYjU5ZjZlMGM5M2Q2MWRmNzMwIiwidXNlcl9pZCI6Mn0.tDW4q6MiVkjqUXf8ltKl7TS0mnIjDyTV0R7LHnMFZ0Q"

headers = {
    "Authorization": f"Bearer {token}"
}

def get_market_milk_price():
    response = requests.get(f'{BASE_URL}/market-milk-prices/', headers=headers)
    print(response.json())

def create_market_milk_price():
    data = {
        "price": 40
    }
    response = requests.post(f'{BASE_URL}/market-milk-prices/', headers=headers, json=data)
    print(response.json())


def update_market_milk_price(price_id):
    data = {
        "price": 50
    }
    response = requests.put(f'{BASE_URL}/market-milk-prices/{price_id}/', headers=headers, json=data)
    print(response.json())


if __name__ == "__main__":
    get_market_milk_price()