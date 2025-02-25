import json
import boto3
import requests
import logging
import random  
from requests_aws4auth import AWS4Auth

# ✅ AWS Configuration
aws_region = "us-east-1"
sqs = boto3.client('sqs', region_name=aws_region)
ses = boto3.client("ses", region_name=aws_region)
dynamodb = boto3.resource('dynamodb', region_name=aws_region)
table = dynamodb.Table('yelp-restaurants')  

# ✅ OpenSearch Public URL
opensearch_url = "https://search-restaurants-search-jjgc45ip6u6h6ldfrrsl7pb4za.us-east-1.es.amazonaws.com/restaurants/_search"

# ✅ AWS Credentials for OpenSearch Auth
session = boto3.Session(region_name=aws_region)
credentials = session.get_credentials()
auth = AWS4Auth(credentials.access_key, credentials.secret_key, aws_region, 'es', session_token=credentials.token)

# ✅ SQS Queue URL
SQS_QUEUE_URL = "https://sqs.us-east-1.amazonaws.com/205930609338/DiningConciergeQueue"

# ✅ Logging Setup
logger = logging.getLogger()
logger.setLevel(logging.INFO)

def get_restaurant_recommendations(cuisine):
    """Fetches restaurant IDs from OpenSearch based on cuisine."""
    logger.info(f"🔍 Querying OpenSearch for cuisine: {cuisine}")

    query = {
        "size": 100,  # ✅ Fetch top 100 matching restaurants
        "query": {
            "match": {
                "cuisine": cuisine
            }
        }
    }

    headers = {"Content-Type": "application/json"}

    try:
        response = requests.get(opensearch_url, auth=auth, headers=headers, json=query)

        if response.status_code != 200:
            logger.error(f"❌ OpenSearch query failed: {response.text}")
            return []

        data = response.json()
        hits = data.get("hits", {}).get("hits", [])

        if not hits:
            logger.warning(f"⚠️ No restaurants found for cuisine: {cuisine}")
            return []

        restaurant_ids = [hit["_source"]["business_id"] for hit in hits]
        
        # ✅ Randomly select 5 restaurants from the 100 retrieved
        selected_restaurants = random.sample(restaurant_ids, min(5, len(restaurant_ids)))

        logger.info(f"✅ OpenSearch returned {len(restaurant_ids)} restaurant IDs, selected: {selected_restaurants}")
        return selected_restaurants

    except Exception as e:
        logger.error(f"❌ Error querying OpenSearch: {str(e)}")
        return []

def get_restaurant_details(business_ids):
    """Fetches restaurant details from DynamoDB."""
    logger.info(f"📡 Fetching details from DynamoDB table 'yelp-restaurants' for {len(business_ids)} restaurants...")

    restaurants = []
    for business_id in business_ids:
        try:
            response = table.get_item(Key={'business_id': business_id})
            if 'Item' in response:
                restaurants.append(response["Item"])
        except Exception as e:
            logger.error(f"❌ Error fetching restaurant {business_id} from DynamoDB: {str(e)}")

    logger.info(f"✅ Successfully fetched {len(restaurants)} restaurants from DynamoDB.")
    return restaurants

def send_email(recipient, cuisine, restaurants):
    """Formats and sends restaurant recommendations via AWS SES."""
    if not restaurants:
        logger.warning("⚠️ No restaurant recommendations to send.")
        return

    subject = f"Your {cuisine} Restaurant Suggestions!"
    body_text = f"Hello! Here are some {cuisine} restaurant recommendations:\n\n"

    for i, r in enumerate(restaurants, 1):
        body_text += f"{i}. {r['name']} - {r['address']} (Rating: {r['rating']})\n"

    body_text += "\nEnjoy your meal!\n\n- Dining Concierge Bot"

    logger.info(f"📤 Sending email to {recipient} via SES...")

    try:
        response = ses.send_email(
            Source="addydiningbot@gmail.com",  # ✅ Verified SES sender email
            Destination={"ToAddresses": [recipient]},
            Message={
                "Subject": {"Data": subject},
                "Body": {"Text": {"Data": body_text}}
            }
        )
        logger.info(f"✅ Email successfully sent to {recipient} | Message ID: {response['MessageId']}")

    except Exception as e:
        logger.error(f"❌ Error sending email to {recipient}: {str(e)}")

def lambda_handler(event, context):
    """Reads SQS messages, fetches restaurant recommendations, and processes them."""
    execution_id = context.aws_request_id
    logger.info(f"🚀 Lambda Execution Started | Execution ID: {execution_id}")

    # ✅ Fetch messages from SQS
    if "Records" in event:
        messages = event["Records"]
    else:
        messages = sqs.receive_message(
            QueueUrl=SQS_QUEUE_URL,
            MaxNumberOfMessages=5,
            WaitTimeSeconds=10,
            VisibilityTimeout=60
        ).get("Messages", [])

    if not messages:
        logger.warning("⚠️ No new messages in SQS.")
        return {"status": "No messages"}

    for message in messages:
        try:
            body = json.loads(message["body"]) if "body" in message else json.loads(message["Body"])
            cuisine = body.get("Cuisine")
            recipient = body.get("Email")

            if not cuisine or not recipient:
                logger.error(f"❌ Invalid message format: {body}")
                continue

            logger.info(f"📩 Processing SQS Message: {message['messageId']} | Cuisine: {cuisine} | Email: {recipient}")

            # ✅ Query OpenSearch for recommendations
            business_ids = get_restaurant_recommendations(cuisine)
            if not business_ids:
                logger.warning(f"⚠️ No recommendations found for {cuisine}")
                continue

            # ✅ Fetch restaurant details from DynamoDB
            restaurant_details = get_restaurant_details(business_ids)
            if restaurant_details:
                # ✅ Send email
                send_email(recipient, cuisine, restaurant_details)

                try:
                    # ✅ Delete SQS message after successful processing
                    sqs.delete_message(
                        QueueUrl=SQS_QUEUE_URL,
                        ReceiptHandle=message["receiptHandle"]
                    )
                    logger.info(f"🗑️ Deleted SQS Message: {message['messageId']}")
                except Exception as e:
                    logger.error(f"⚠️ Failed to delete SQS message {message['messageId']}: {str(e)}")
            else:
                logger.warning(f"⚠️ No restaurant data found for {cuisine}. Not deleting SQS message.")

        except Exception as e:
            logger.error(f"⚠️ Error processing SQS message: {str(e)}")

    return {"status": "Processed messages"}
