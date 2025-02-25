import requests
from requests_aws4auth import AWS4Auth
import boto3
import json

# ✅ AWS Configuration
aws_region = "us-east-1"  # Change if your OpenSearch is in a different region
opensearch_url = "https://search-restaurants-search-jjgc45ip6u6h6ldfrrsl7pb4za.us-east-1.es.amazonaws.com/restaurants"

# ✅ Get AWS credentials
session = boto3.Session(region_name=aws_region)
credentials = session.get_credentials()
auth = AWS4Auth(credentials.access_key, credentials.secret_key, aws_region, 'es', session_token=credentials.token)

# ✅ Define Index Settings & Mappings
index_settings = {
    "settings": {
        "number_of_shards": 2,  # Adjust based on cluster size
        "number_of_replicas": 1  # Use 1 if cluster has 2 data nodes
    },
    "mappings": {
        "properties": {
            "business_id": {"type": "keyword"},
            "cuisine": {"type": "text"}
        }
    }
}

# ✅ Send a signed PUT request to create the index
headers = {"Content-Type": "application/json"}
response = requests.put(opensearch_url, auth=auth, json=index_settings, headers=headers)

# ✅ Print the response
print("Response Code:", response.status_code)
print("Response:", json.dumps(response.json(), indent=2))