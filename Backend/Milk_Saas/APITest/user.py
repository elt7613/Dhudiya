import requests

# API endpoints
BASE_URL = 'http://127.0.0.1:8000/api'
REGISTER_URL = f'{BASE_URL}/register/'
LOGIN_URL = f'{BASE_URL}/login/'

'{BASE_URL}/apply-referral/'


token = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ0b2tlbl90eXBlIjoiYWNjZXNzIiwiZXhwIjoxNzQyNDY1NDIzLCJpYXQiOjE3Mzk4NzM0MjMsImp0aSI6ImY4NTAzZjQwMTdiNTQ2NTU5ZmViNjVjYTYzMzZiYWYxIiwidXNlcl9pZCI6Nn0.2dJjMBTyCX4DwA5n9Qdep-T5i5MxyzJa3ZU6qgWC9Yc"

headers = {
    "Authorization": f"Bearer {token}",
    'Content-Type': 'application/json'
}


def register_user():
    data = {
        "username": "Ema",
        "phone_number": "1203654789",
        "email": "emmanuele7613@gmail.com",
        "password": "Password123",
        #"referral_code": ""
    }
    response = requests.post(REGISTER_URL, json=data)
    print("Registration Response:", response.json())
    return response.json()

def login_user(login_field, password):
    data = {
        "login_field": login_field,  # Can be username or phone number
        "password": password
    }
    response = requests.post(LOGIN_URL, json=data)
    print("Login Response:", response.json())
    return response.json().get('token')

def test_auth_flow():
    # Register new user
    register_response = register_user()
    
    # Login with username
    token = login_user("kun", "Password123")

    # Login with phone number
    #token = login_user("+911034567893", "NewPassword123")
    
    return token


def forget_password():
    data = {
        "email": "elt7613@gmail.com"
    }
    response = requests.post(f"{BASE_URL}/forgot-password/", json=data)
    print("Forget Password Response:", response.json())
    return response.json()

def reset_password():
    data = {
        "email": "xaioene@gmail.com",
        "otp": "325972",
        "new_password": "NewPassword123"
    }
    response = requests.post(f"{BASE_URL}/reset-password/", json=data)
    print("Reset Password Response:", response.json())
    return response.json()

def apply_referral_code():
    data = {
        "referral_code": "IPD04"
    }
    response = requests.post(f"{BASE_URL}/apply-referral/", json=data, headers=headers)
    print("Apply Referral Code Response:", response.json())
    return response.json()

def get_user_info():
    response = requests.get(f"{BASE_URL}/info/", headers=headers)
    print("Get User Info Response:", response.json())
    return response.json()

if __name__ == "__main__":
    apply_referral_code()