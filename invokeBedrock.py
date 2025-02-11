import json
import boto3
import os
import re

REGION_NAME = os.environ["REGION_NAME"]
INFERENCE_PROFILE_ID = os.environ["INFERENCE_PROFILE_ID"]
SECRET_NAME = os.environ["SECRET_NAME"]


def bedrock_call(inputText, sessionId):
    sm_client = boto3.client("secretsmanager", region_name=REGION_NAME)

    def get_secret(secret_name):
        # Create a Secrets Manager client
        try:
            # Retrieve the secret value
            response = sm_client.get_secret_value(SecretId=secret_name)
        except Exception as e:
            # Handle errors (e.g., secret not found, access denied)
            print(f"Error retrieving secret: {e}")
            raise e
        else:
            # Parse the secret string
            if "SecretString" in response:
                secret = response["SecretString"]
                return json.loads(secret)  # Convert JSON string to a dictionary
            else:
                # If the secret is binary, decode it
                decoded_binary_secret = base64.b64decode(response["SecretBinary"])
                return decoded_binary_secret

    secret = get_secret(SECRET_NAME)

    bedrock_runtime = boto3.client(
        service_name="bedrock-runtime",
        region_name=REGION_NAME,
        aws_access_key_id=secret["AWS_ACCESS_KEY"],
        aws_secret_access_key=secret["AWS_SECRET_KEY"],
    )

    try:
        response = bedrock_runtime.converse(
            modelId=INFERENCE_PROFILE_ID,
            # system = [{"text": system_prompt}],
            messages=[{"role": "user", "content": [{"text": inputText}]}],
        )

        print(response["output"]["message"]["content"])
        return response
    except Exception as e:
        print("unexpected event.", e)
        return "Internal Server Error: " + str(e)


def lambda_handler(event, context):
    try:
        bodyObj = json.loads(event["body"])
        inputText = bodyObj["inputText"]
        sessionId = bodyObj["sessionId"]
    except:
        return {"statusCode": 400, "body": json.dumps({"error": "Invalid JSON"})}

    response = bedrock_call(inputText, sessionId)

    return {"statusCode": 200, "body": json.dumps(response)}
