import json
import os

import boto3
from dotenv import load_dotenv
from secrets_manager import get_agent_runtime_arn

# Load environment variables from .env file
load_dotenv()

# Get configuration from environment variables or AWS Secrets Manager
AWS_REGION = os.getenv("AWS_REGION", "us-east-1")

# Try to get ARN from environment variable first (for local dev),
# then fall back to AWS Secrets Manager (for production)
AGENT_RUNTIME_ARN = os.getenv("AGENT_RUNTIME_ARN")

if not AGENT_RUNTIME_ARN:
    print(
        "AGENT_RUNTIME_ARN not found in environment, fetching from AWS Secrets Manager..."
    )
    try:
        AGENT_RUNTIME_ARN = get_agent_runtime_arn(region_name=AWS_REGION)
        print("✓ Successfully retrieved ARN from AWS Secrets Manager")
    except Exception as e:
        raise ValueError(
            f"Failed to retrieve AGENT_RUNTIME_ARN: {str(e)}\n"
            "Please set it in your .env file or ensure the secret exists in AWS Secrets Manager."
        ) from e
else:
    print("✓ Using AGENT_RUNTIME_ARN from environment variable")

client = boto3.client("bedrock-agentcore", region_name=AWS_REGION)
payload = json.dumps(
    {"prompt": "Search for flights from JFK to LAX on 2025-10-20 for 1 passenger"}
)

response = client.invoke_agent_runtime(
    agentRuntimeArn=AGENT_RUNTIME_ARN,
    runtimeSessionId="dfmeoagmreaklgmrkleafremoigrmtesogmtrskhmtkrlshmz",  # Must be 33+ chars
    payload=payload,
    qualifier="DEFAULT",  # Optional
)
response_body = response["response"].read()
response_data = json.loads(response_body)
print("Agent Response:", response_data)
