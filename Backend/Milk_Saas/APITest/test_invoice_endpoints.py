import requests
from datetime import datetime, timedelta
import json

# Base URL and authentication
BASE_URL = "http://127.0.0.1:8000/api/collector"

token = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ0b2tlbl90eXBlIjoiYWNjZXNzIiwiZXhwIjoxNzQyMDMzODQwLCJpYXQiOjE3Mzk0NDE4NDAsImp0aSI6IjBhZTcxMDIwYzc2YTRiYzk5MjJiMGZhYzI5MmEzZjQxIiwidXNlcl9pZCI6Mn0.xUjr1j0fodfvJPkt-SL6eYm8zIBfeIKprb7-IX7MGEU"


headers = {
    "Authorization": f"Bearer {token}",
    "Content-Type": "application/json"
}

# Get dates for the last 7 days
end_date = datetime.now().date()
start_date = end_date - timedelta(days=7)

# Format dates as strings
date_from = start_date.strftime("%Y-%m-%d")
date_to = end_date.strftime("%Y-%m-%d")

def save_pdf(response, filename):
    if response.status_code == 200:
        with open(filename, 'wb') as f:
            f.write(response.content)
        print(f"Successfully saved {filename}")
    else:
        print(f"Error: {response.status_code}")
        print(response.text)

# 1. Purchase Report
def get_purchase_report():
    url = f"{BASE_URL}/collections/purchase_report/"
    params = {
        "date_from": date_from,
        "date_to": date_to
    }
    
    response = requests.get(url, headers=headers, params=params)
    save_pdf(response, "purchase_report.pdf")

# 2. Milk Purchase Summary
def get_milk_purchase_summary():
    url = f"{BASE_URL}/collections/milk_purchase_summary/"
    params = {
        "date_from": date_from,
        "date_to": date_to
    }
    
    response = requests.get(url, headers=headers, params=params)
    save_pdf(response, "milk_purchase_summary.pdf")

# 3. Milk Bill (for a specific customer)
def get_milk_bill(customer_id):
    url = f"{BASE_URL}/collections/milk_bill/"
    params = {
        "customer_id": customer_id,
        "date_from": date_from,
        "date_to": date_to
    }
    
    response = requests.get(url, headers=headers, params=params)
    save_pdf(response, f"milk_bill_customer_{customer_id}.pdf")

if __name__ == "__main__":
    # Get all three types of reports
    print("Generating Purchase Report...")
    get_purchase_report()
    
    print("\nGenerating Milk Purchase Summary...")
    get_milk_purchase_summary()
    
    print("\nGenerating Milk Bill for customer...")
    customer_id = 1  # Replace with actual customer ID
    get_milk_bill(customer_id) 