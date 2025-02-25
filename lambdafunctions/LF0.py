import json
import boto3
import logging

# Configure logging
logger = logging.getLogger()
logger.setLevel(logging.DEBUG)

# Initialize Lex client (V1)
lex_client = boto3.client('lex-runtime')

def lambda_handler(event, context):
    """
    Handles API Gateway requests and routes them to Lex.
    """

    # ✅ Extract and validate input message
    body = event.get("body", {})
    if isinstance(body, str):  # API Gateway might send body as a string
        try:
            body = json.loads(body)
        except json.JSONDecodeError:
            return {
                "statusCode": 400,
                "headers": {"Content-Type": "application/json"},
                "body": json.dumps({"message": "Invalid JSON format."})
            }

    user_message = body.get("message", "").strip()

    if not user_message:
        return {
            "statusCode": 400,
            "headers": {"Content-Type": "application/json"},
            "body": json.dumps({"message": "Invalid input, please provide a message."})
        }

    # ✅ Send user message to Lex
    try:
        lex_response = lex_client.post_text(
            botName="DiningConceirgeBot",  # ✅ Ensure this matches your Lex V1 bot name
            botAlias="prod",               # ✅ Ensure this alias exists and is published
            userId="test-user",             # Can be dynamic (from session, user context, etc.)
            inputText=user_message          # User's message
        )

        # ✅ Extract response from Lex
        lex_message = lex_response.get("message", "I'm not sure how to respond.")

        return {
            "statusCode": 200,
            "headers": {"Content-Type": "application/json"},
            "body": json.dumps({"message": lex_message})
        }

    except lex_client.exceptions.NotFoundException:
        return {
            "statusCode": 500,
            "headers": {"Content-Type": "application/json"},
            "body": json.dumps({"message": "Error: Lex bot alias not found. Ensure the alias 'prod' is published."})
        }

    except lex_client.exceptions.AccessDeniedException:
        return {
            "statusCode": 403,
            "headers": {"Content-Type": "application/json"},
            "body": json.dumps({"message": "Error: Lambda does not have permission to call Lex. Update the IAM role."})
        }

    except Exception as e:
        logger.error(f"Unexpected error: {str(e)}")
        return {
            "statusCode": 500,
            "headers": {"Content-Type": "application/json"},
            "body": json.dumps({"message": "An unexpected error occurred while communicating with bot."})
        }
