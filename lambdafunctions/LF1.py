import datetime
import logging
import json
import boto3

# Configure logging
logger = logging.getLogger()
logger.setLevel(logging.DEBUG)

# Initialize SQS client
sqs = boto3.client('sqs')
SQS_QUEUE_URL = "https://sqs.us-east-1.amazonaws.com/205930609338/DiningConciergeQueue"

""" --- Helpers to build responses which match the structure of the necessary dialog actions --- """

def get_slots(intent_request):
    """ Extracts slot values from Lex event """
    return intent_request['currentIntent']['slots']

def elicit_slot(session_attributes, intent_name, slots, slot_to_elicit, message):
    """ Prompts the user for the missing slot """
    return {
        'sessionAttributes': session_attributes,
        'dialogAction': {
            'type': 'ElicitSlot',
            'intentName': intent_name,
            'slots': slots,
            'slotToElicit': slot_to_elicit,
            'message': message
        }
    }

def close(session_attributes, fulfillment_state, message):
    """ Closes the conversation with the user """
    return {
        'sessionAttributes': session_attributes,
        'dialogAction': {
            'type': 'Close',
            'fulfillmentState': fulfillment_state,
            'message': message
        }
    }

def delegate(session_attributes, slots):
    """ Lets Lex take over the conversation if all slots are filled """
    return {
        'sessionAttributes': session_attributes,
        'dialogAction': {
            'type': 'Delegate',
            'slots': slots
        }
    }

""" --- Helper Functions --- """

def build_validation_result(is_valid, violated_slot, message_content):
    """ Builds a validation response for Lex """
    return {
        'isValid': is_valid,
        'violatedSlot': violated_slot,
        'message': {'contentType': 'PlainText', 'content': message_content}
    }

def validate_dining_suggestion(location, cuisine, dining_date, dining_time, party_size, email):
    """ Validates user inputs """

    logger.debug(f"Validating inputs: Location={location}, Cuisine={cuisine}, DiningDate={dining_date}, DiningTime={dining_time}, PartySize={party_size}, Email={email}")

    valid_locations = ["manhattan", "new york", "nyc", "new york city", "ny"]
    valid_cuisines = ["chinese", "indian", "italian", "japanese", "mexican", "thai", "korean", "arab", "american","pakistani","greek","spanish","turkish","french","indonesian"]

    # ✅ Location validation
    if location:
        if location.lower() not in valid_locations:
            return build_validation_result(False, 'Location', f'Sorry, we do not provide service in "{location}". Please enter Manhattan or NYC.')

    # ✅ Cuisine validation
    if cuisine:
        if cuisine.lower() not in valid_cuisines:
            return build_validation_result(False, 'Cuisine', f'Sorry, we do not have suggestions for "{cuisine}". Please choose another cuisine.')

    # ✅ Date validation (Supports "today", "tomorrow", or "YYYY-MM-DD")
    today = datetime.date.today()
    if dining_date:
        if dining_date.lower() == "today":
            dining_date = today.strftime("%Y-%m-%d")
        elif dining_date.lower() == "tomorrow":
            dining_date = (today + datetime.timedelta(days=1)).strftime("%Y-%m-%d")
        elif dining_date.lower() == "yesterday":
            return build_validation_result(False, 'DiningDate', 'You cannot select a past date. Please enter a valid date, "today", or "tomorrow".')
        else:
            try:
                parsed_date = datetime.datetime.strptime(dining_date, "%Y-%m-%d").date()
                if parsed_date < today:
                    return build_validation_result(False, 'DiningDate', 'You cannot select a past date. Please enter a valid date, "today", or "tomorrow".')
            except ValueError:
                return build_validation_result(False, 'DiningDate', 'Invalid date format. Please enter a valid date (YYYY-MM-DD), "today", or "tomorrow".')

    # ✅ Time validation
    if dining_time:
        try:
            parsed_time = datetime.datetime.strptime(dining_time, "%H:%M")
            hour = parsed_time.hour
            if hour < 10 or hour > 23:
                return build_validation_result(False, 'DiningTime', 'Our business hours are from 10 AM to 11 PM. Please enter a valid time in HH:MM format.')
        except ValueError:
            return build_validation_result(False, 'DiningTime', 'Invalid time format. Please enter a valid time in HH:MM format (e.g., 18:30 for 6:30 PM).')

    # ✅ Party size validation
    if party_size:
        try:
            party_size = int(party_size)
            if party_size < 1 or party_size > 15:
                return build_validation_result(False, 'PartySize', 'Sorry! We accept reservations only for up to 15 people.')
        except ValueError:
            return build_validation_result(False, 'PartySize', 'Invalid entry. Please enter a valid number for party size.')

    # ✅ Email validation
    if email:
        if "@" not in email or "." not in email or " " in email:
            return build_validation_result(False, 'Email', 'Invalid entry. Please provide a valid email address.')

    return build_validation_result(True, None, None)

""" --- Functions that control the bot's behavior --- """

def dining_suggestions_intent(intent_request):
    """ Handles DiningSuggestionsIntent """
    slots = get_slots(intent_request)
    session_attributes = intent_request.get('sessionAttributes', {})

    location = slots.get('Location')
    cuisine = slots.get('Cuisine')
    dining_date = slots.get('DiningDate')
    dining_time = slots.get('DiningTime')
    party_size = slots.get('PartySize')
    email = slots.get('Email')

    source = intent_request.get('invocationSource', 'Fulfillment')

    logger.debug(f"Invocation Source: {source}")

    if source == 'DialogCodeHook':
        validation_result = validate_dining_suggestion(location, cuisine, dining_date, dining_time, party_size, email)
        if not validation_result['isValid']:
            slots[validation_result['violatedSlot']] = None
            return elicit_slot(session_attributes, intent_request['currentIntent']['name'], slots,
                               validation_result['violatedSlot'], validation_result['message'])

        return delegate(session_attributes, slots)

    # Send data to SQS Queue
    sqs.send_message(
        QueueUrl=SQS_QUEUE_URL,
        MessageBody=json.dumps({
            "Location": location,
            "Cuisine": cuisine,
            "DiningDate": dining_date,
            "DiningTime": dining_time,
            "PartySize": party_size,
            "Email": email
        })
    )

    confirmation_message = f"Thank you! I will send restaurant suggestions for {cuisine} cuisine in {location} on {dining_date} at {dining_time} for {party_size} people. You will receive the details at {email}."

    return close(session_attributes, "Fulfilled", {'contentType': 'PlainText', 'content': confirmation_message})

def dispatch(intent_request):
    """ Routes request to the correct intent handler """
    intent_name = intent_request['currentIntent']['name']
    logger.debug(f"Dispatching intent: {intent_name}")

    if intent_name == 'DiningSuggestionsIntent':
        return dining_suggestions_intent(intent_request)
    elif intent_name == 'ThankYouIntent':
        return close({}, "Fulfilled", {'contentType': 'PlainText', 'content': "You're welcome! Let me know if you need anything else."})
    elif intent_name == 'GreetingIntent':
        return close({}, "Fulfilled", {'contentType': 'PlainText', 'content': "Hi there! How can I assist you today?"})

    raise Exception(f'Intent with name {intent_name} not supported')

def lambda_handler(event, context):
    """ AWS Lambda main function """
    logger.debug(f"Received event: {json.dumps(event)}")
    return dispatch(event)
