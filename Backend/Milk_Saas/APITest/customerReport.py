import requests
from datetime import datetime

BASE_URL = 'http://127.0.0.1:8000/api/collector'

token = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ0b2tlbl90eXBlIjoiYWNjZXNzIiwiZXhwIjoxNzQyNDY1NDIzLCJpYXQiOjE3Mzk4NzM0MjMsImp0aSI6ImY4NTAzZjQwMTdiNTQ2NTU5ZmViNjVjYTYzMzZiYWYxIiwidXNlcl9pZCI6Nn0.2dJjMBTyCX4DwA5n9Qdep-T5i5MxyzJa3ZU6qgWC9Yc"

headers = {
    "Authorization": f"Bearer {token}"
}

def generate_report(start_date, end_date, customer_ids):
    response = requests.get(
        f'{BASE_URL}/collections/generate_customer_report/',
        params={'start_date': start_date, 'end_date': end_date, 'customer_ids': customer_ids},
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
generate_report('2025-02-21', '2025-02-25', '2')