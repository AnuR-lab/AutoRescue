"""Utility to load encrypted personal_info.json from S3.

"""
from __future__ import annotations
import json
from functools import lru_cache
from typing import Any, Dict
import boto3

DEFAULT_BUCKET = "autorescue-personal-info"
DEFAULT_KEY = "personal_info.json"
DEFAULT_PROFILE = "SBPOC11"

class PersonalInfoLoaderError(Exception):
    """Raised when the S3 object cannot be retrieved or parsed."""

@lru_cache(maxsize=32)
def _get_s3_client(profile_name: str | None = None):
    if profile_name:
        session = boto3.Session(profile_name=profile_name)
        return session.client("s3")
    return boto3.client("s3")

def load_personal_info(bucket: str = DEFAULT_BUCKET, key: str = DEFAULT_KEY, *, use_cache: bool = True, profile_name: str = DEFAULT_PROFILE) -> Dict[str, Any]:
    """Load personal info JSON from S3.

    Parameters
    ----------
    bucket: str
        S3 bucket name (encrypted at rest via KMS per CF template).
    key: str
        Object key (defaults to personal_info.json).
    use_cache: bool
        If True, caches parsed JSON during process lifetime.

    Returns
    -------
    dict
        Parsed JSON content.

    Raises
    ------
    PersonalInfoLoaderError
        On missing object, access denied, or JSON parse failure.
    """
    s3 = _get_s3_client(profile_name if use_cache else None) if use_cache else (
        boto3.Session(profile_name=profile_name).client("s3") if profile_name else boto3.client("s3")
    )
    try:
        obj = s3.get_object(Bucket=bucket, Key=key)
    except Exception as e:  # broad capture, rewrap
        raise PersonalInfoLoaderError(f"Failed to get s3://{bucket}/{key}: {e}") from e

    try:
        body = obj["Body"].read()
        return json.loads(body)
    except Exception as e:  # parse errors
        raise PersonalInfoLoaderError(f"Failed to parse JSON for s3://{bucket}/{key}: {e}") from e

if __name__ == "__main__":  # simple CLI
    import argparse
    parser = argparse.ArgumentParser(description="Load personal_info.json from S3 and print to stdout")
    parser.add_argument("--bucket", default=DEFAULT_BUCKET)
    parser.add_argument("--key", default=DEFAULT_KEY)
    parser.add_argument("--no-cache", action="store_true", help="Disable client cache")
    parser.add_argument("--profile", help="AWS profile name (e.g. SBPOC11)")
    args = parser.parse_args()
    data = load_personal_info()
    print(json.dumps(data, indent=2))
