#!/usr/bin/env python3
"""
Utility functions for retrieving secrets from AWS Secrets Manager
"""

import boto3
import json
from typing import Optional


def get_secret(secret_name: str, region_name: str = "us-east-1") -> dict:
    """
    Retrieve a secret from AWS Secrets Manager
    
    Args:
        secret_name: Name of the secret to retrieve
        region_name: AWS region (default: us-east-1)
    
    Returns:
        dict: The secret value as a dictionary
    
    Raises:
        Exception: If secret cannot be retrieved
    """
    client = boto3.client('secretsmanager', region_name=region_name)
    
    try:
        response = client.get_secret_value(SecretId=secret_name)
        
        if 'SecretString' in response:
            return json.loads(response['SecretString'])
        else:
            raise ValueError(f"Secret {secret_name} does not contain a string value")
            
    except Exception as e:
        raise Exception(f"Failed to retrieve secret {secret_name}: {str(e)}")


def get_agent_runtime_arn(region_name: str = "us-east-1") -> str:
    """
    Retrieve the Agent Runtime ARN from AWS Secrets Manager
    
    Args:
        region_name: AWS region (default: us-east-1)
    
    Returns:
        str: The agent runtime ARN
    
    Raises:
        Exception: If the ARN cannot be retrieved or is not found
    """
    secret = get_secret("autorescue/agent-runtime-arn", region_name)
    arn = secret.get("arn")
    
    if not arn:
        raise ValueError("Agent Runtime ARN not found in secret")
    
    return arn


def get_amadeus_credentials(region_name: str = "us-east-1") -> dict:
    """
    Retrieve Amadeus API credentials from AWS Secrets Manager
    
    Args:
        region_name: AWS region (default: us-east-1)
    
    Returns:
        dict: Dictionary containing client_id and client_secret
    """
    return get_secret("autorescue/amadeus/credentials", region_name)


def get_cognito_credentials(region_name: str = "us-east-1") -> dict:
    """
    Retrieve Cognito OAuth credentials from AWS Secrets Manager
    
    Args:
        region_name: AWS region (default: us-east-1)
    
    Returns:
        dict: Dictionary containing client_id, client_secret, and domain
    """
    return get_secret("autorescue/cognito/credentials", region_name)


# Cache for secrets to avoid repeated API calls
_secret_cache = {}


def get_secret_cached(secret_name: str, region_name: str = "us-east-1", ttl_seconds: int = 3600) -> dict:
    """
    Retrieve a secret from AWS Secrets Manager with caching
    
    Args:
        secret_name: Name of the secret to retrieve
        region_name: AWS region (default: us-east-1)
        ttl_seconds: Time-to-live for cache in seconds (default: 3600 = 1 hour)
    
    Returns:
        dict: The secret value as a dictionary
    """
    import time
    
    cache_key = f"{region_name}:{secret_name}"
    
    # Check if we have a cached value that's still valid
    if cache_key in _secret_cache:
        cached_value, cached_time = _secret_cache[cache_key]
        if time.time() - cached_time < ttl_seconds:
            return cached_value
    
    # Fetch from Secrets Manager
    secret_value = get_secret(secret_name, region_name)
    
    # Cache it
    _secret_cache[cache_key] = (secret_value, time.time())
    
    return secret_value
