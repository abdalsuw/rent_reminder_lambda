import json
import boto3
import logging
from botocore.exceptions import ClientError
from datetime import datetime

#Logging
logger = logging.getLogger()
logger.setLevel(logging.INFO)

# Initialize DynamoDB resource
dynamodb = boto3.resource('dynamodb')

def get_tenant_information(building_unit):
    """Retrieve tenant information from the DynamoDB table."""
    table = dynamodb.Table('tenants')
    
    try:
        response = table.get_item(Key={'building_unit': building_unit})
        return response.get('Item')
    except ClientError as e:
        logger.error(f"Unable to get tenant info for {building_unit:}: {e}")
        return None

def lambda_handler(event, context):
    """AWS Lambda handler function to send rent due reminders."""
    # Retrieve the building unit from the event
    building_unit = event.get('building_unit')
    
    if not building_unit:
        logger.warning('No building_unit provided in the event')
        return {
            'statusCode': 400,
            'body': json.dumps({'error': 'Missing building_unit in the event'})
        }

    # Get tenant info from DynamoDB
    tenant_information = get_tenant_information(building_unit)
    
    if not tenant_information:
        logger.info(f"No tenant info found for {building_unit}")
        return {
            'statusCode': 404,
            'body': json.dumps({'error': f'No tenant information found for {building_unit}'})
        }

    # Extract tenant information with default values
    tenant_name = tenant_information.get('tenant_name', 'Unknown Tenant')
    phone_number = tenant_information.get('phone_number', 'N/A')
    rent_price = tenant_information.get('rent_price', '0.00')
    
    current_month = datetime.now().strftime("%B")

    # Define due and reminder dates
    due_date = f"5th of {current_month}"  # The due date is always the 5th of the current month
    reminder_date = f"1st of {current_month}"  # Reminder for the 1st of each month

    # reminder_message creation
    reminder_message = (f"Hello {tenant_name}, this is a friendly reminder that your rent for {current_month} is due on or before {due_date}. "
           f"The total amount due is ${rent_price:.2f}. "
           f"If paid late, a fee of $35 will be added on the first day, and $25 for each day after that. "
           f"Please make sure to pay it on time. If you have any questions, feel free to contact [Contact Info].")
           
    # Initialize SNS client
    client = boto3.client("sns")

    try:
        # Publish reminder_message to SNS
        response = client.publish(
            PhoneNumber=phone_number,
            Message=json.dumps({
                "event": "rent_due_reminder",
                "tenant_name": tenant_name,
                "due_date": due_date,
                "reminder_date": reminder_date,
                "reminder_message": reminder_message
            }),
        )
        logger.info(f"reminder_message sent to {tenant_name} at {phone_number}")

        return {
            'statusCode': 200,
            'body': json.dumps(response)
        }

    except Exception as e:
        logger.error(f"Failed to send reminder_message to {tenant_name} at {phone_number}: {e}")
        return {
            'statusCode': 500,
            'body': json.dumps({'error': str(e)})
        }

# DynamoDB write_to_db stub (if needed later)
def write_to_db(event):
    pass
