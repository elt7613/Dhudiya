import requests

# API endpoints
BASE_URL = 'http://127.0.0.1:8000/api'
REGISTER_URL = f'{BASE_URL}/register/'
LOGIN_URL = f'{BASE_URL}/login/'

def register_user():
    data = {
        "username": "xaioene",
        "phone_number": "+9198764320",
        "email": "xaioene@gmail.com",
        "password": "Password123"
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
    token = login_user("xaioene", "NewPassword123")

    # Login with phone number
    token = login_user("+9198764320", "NewPassword123")
    
    return token


def forget_password():
    data = {
        "email": "xaioene@gmail.com"
    }
    response = requests.post(f"{BASE_URL}/forgot-password/", json=data)
    print("Forget Password Response:", response.json())
    return response.json()

def reset_password():
    data = {
        "email": "xaioene@gmail.com",
        "otp": "376879",
        "new_password": "NewPassword123"
    }
    response = requests.post(f"{BASE_URL}/reset-password/", json=data)
    print("Reset Password Response:", response.json())
    return response.json()

if __name__ == "__main__":
    test_auth_flow()