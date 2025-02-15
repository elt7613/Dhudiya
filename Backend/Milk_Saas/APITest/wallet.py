import requests

url = "http://127.0.0.1:8000/api/wallet"

token = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ0b2tlbl90eXBlIjoiYWNjZXNzIiwiZXhwIjoxNzQyMTE4NDYwLCJpYXQiOjE3Mzk1MjY0NjAsImp0aSI6ImM4NGM4N2FhYzVmZjQ0ZWQ5OGQ4ZWQ0NjJiNjEwOGU0IiwidXNlcl9pZCI6M30.9yAKs1hQlUjjv0Jl4P5SnV4JEgIfJbOxx46NUhjDiIg"

headers = {
    "Authorization": f"Bearer {token}"
}

def get_wallet():
    response = requests.get(url, headers=headers)
    print(response.json())

def get_transactions():
    response = requests.get(f"{url}/transactions/", headers=headers)
    print(response.json())

def add_money():
    data = {
        "amount": 50,
    }
    response = requests.post(f"{url}/add_money/", headers=headers, json=data)
    print(response.json())

def verify_payment(id):
    data = {
        "payment_link_id": id
    }

    response = requests.post(f"{url}/verify_payment/", headers=headers, json=data)
    print(response.json())

if __name__ == "__main__":
    get_wallet()
   # add_money()
  #verify_payment("plink_Pw09TkxrV6N9kg")
  #get_transactions()