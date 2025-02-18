import requests
from datetime import datetime

BASE_URL = 'http://127.0.0.1:8000/api/collector'

token = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ0b2tlbl90eXBlIjoiYWNjZXNzIiwiZXhwIjoxNzQyNDY1NDIzLCJpYXQiOjE3Mzk4NzM0MjMsImp0aSI6ImY4NTAzZjQwMTdiNTQ2NTU5ZmViNjVjYTYzMzZiYWYxIiwidXNlcl9pZCI6Nn0.2dJjMBTyCX4DwA5n9Qdep-T5i5MxyzJa3ZU6qgWC9Yc"

headers = {
    "Authorization": f"Bearer {token}"
}

def generate_invoice(start_date, end_date):
    """
    Generate a milk collection report for the given date range
    
    Args:
        start_date (str): Start date in YYYY-MM-DD format
        end_date (str): End date in YYYY-MM-DD format
    """
    response = requests.get(
        f'{BASE_URL}/collections/generate_report/',
        params={
            'start_date': start_date,
            'end_date': end_date
        },
        headers=headers
    )
    
    if response.status_code == 200:
        filename = f"milk_report_{start_date}_to_{end_date}.pdf"
        
        # Save the PDF
        with open(filename, 'wb') as f:
            f.write(response.content)
        print(f"Report saved as {filename}")
    else:
        # If there's an error, try to parse the JSON error message
        try:
            error_data = response.json()
            print(f"Error: {error_data}")
        except:
            print(f"Error: {response.status_code} - {response.text}")

# Example usage - just provide the dates
generate_invoice('2025-02-22', '2025-02-25')

# Example for generating other report types:
# generate_invoice('2025-02-22', '2025-02-25', 'milk_purchase_summary')
# For customer bill (requires customer parameter):
# generate_invoice('2025-02-22', '2025-02-25', 'customer_milk_bill')

