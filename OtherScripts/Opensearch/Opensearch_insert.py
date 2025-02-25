import json  # ✅ Import json
import boto3
import requests
from requests_aws4auth import AWS4Auth

# ✅ AWS Configuration
aws_region = "us-east-1"
session = boto3.Session(region_name=aws_region)
credentials = session.get_credentials()

# Ensure credentials are retrieved properly
if credentials is None:
    raise ValueError("AWS credentials could not be retrieved. Check IAM permissions.")

auth = AWS4Auth(
    credentials.access_key,
    credentials.secret_key,
    aws_region,
    'es',
    session_token=credentials.token
)

# ✅ Updated OpenSearch URL (Consistent with Index Creation Script)
opensearch_url = "https://search-restaurants-search-jjgc45ip6u6h6ldfrrsl7pb4za.us-east-1.es.amazonaws.com/restaurants/_bulk"

# ✅ Initialize DynamoDB
dynamodb = boto3.resource('dynamodb', region_name=aws_region)
table = dynamodb.Table('yelp-restaurants')

def insert_into_opensearch():
    """Fetches restaurants from DynamoDB and inserts into OpenSearch."""
    response = table.scan()
    items = response.get('Items', [])

    if not items:
        print("❌ No data found in DynamoDB!")
        return

    bulk_data = ""

    for item in items:
        business_id = item.get("business_id", "UNKNOWN")
        cuisine = item.get("cuisine", "UNKNOWN")  # FIX: Ensures cuisine is not None

        if cuisine == "UNKNOWN":
            print(f"⚠️ Skipping {business_id} (No cuisine found)")
            continue  # Skip restaurants without cuisine

        # ✅ Prepare JSON structure
        action = {"index": {"_index": "restaurants", "_id": business_id}}
        data = {"business_id": business_id, "cuisine": cuisine}

        bulk_data += f"{json.dumps(action)}\n{json.dumps(data)}\n"

    if not bulk_data:
        print("❌ No valid records to insert.")
        return

    # ✅ Send Bulk Request
    headers = {"Content-Type": "application/json"}
    response = requests.post(opensearch_url, auth=auth, data=bulk_data, headers=headers)

    # ✅ Print response
    print(response.text)

# ✅ Run function
insert_into_opensearch()