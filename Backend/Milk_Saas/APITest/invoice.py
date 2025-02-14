import requests
from datetime import datetime

BASE_URL = 'http://127.0.0.1:8000/api/collector'

token = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ0b2tlbl90eXBlIjoiYWNjZXNzIiwiZXhwIjoxNzQyMTE4NDYwLCJpYXQiOjE3Mzk1MjY0NjAsImp0aSI6ImM4NGM4N2FhYzVmZjQ0ZWQ5OGQ4ZWQ0NjJiNjEwOGU0IiwidXNlcl9pZCI6M30.9yAKs1hQlUjjv0Jl4P5SnV4JEgIfJbOxx46NUhjDiIg"

headers = {
    "Authorization": f"Bearer {token}"
}

def generate_invoice(start_date, end_date):
    response = requests.get(
        f'{BASE_URL}/collections/generate_invoice/',
        params={'start_date': start_date, 'end_date': end_date},
        headers=headers
    )
    
    if response.status_code == 200:
        # Get filename from Content-Disposition header or create a default one
        filename = f"milk_invoice_{start_date}_to_{end_date}.pdf"
        
        # Save the PDF
        with open(filename, 'wb') as f:
            f.write(response.content)
        print(f"Invoice saved as {filename}")
    else:
        # If there's an error, try to parse the JSON error message
        try:
            error_data = response.json()
            print(f"Error: {error_data}")
        except:
            print(f"Error: {response.status_code} - {response.text}")

# Test the function
generate_invoice('2025-02-14', '2025-02-21')