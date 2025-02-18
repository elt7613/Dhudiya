import requests

url = "http://127.0.0.1:8000/api/wallet"

token = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ0b2tlbl90eXBlIjoiYWNjZXNzIiwiZXhwIjoxNzQyNDY1NDIzLCJpYXQiOjE3Mzk4NzM0MjMsImp0aSI6ImY4NTAzZjQwMTdiNTQ2NTU5ZmViNjVjYTYzMzZiYWYxIiwidXNlcl9pZCI6Nn0.2dJjMBTyCX4DwA5n9Qdep-T5i5MxyzJa3ZU6qgWC9Yc"

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
        "amount":20,
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
    #get_wallet()
  #add_money()
 verify_payment("plink_Px9yeX4GZo6kDP")
  #get_transactions()