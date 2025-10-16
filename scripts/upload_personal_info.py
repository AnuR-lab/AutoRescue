"""Upload local personal_info.json into the autorescue-personal-info S3 bucket.

Usage (PowerShell):
    python scripts/upload_personal_info.py --file c:\path\to\personal_info.json \
        --bucket autorescue-personal-info --key personal_info.json

Requires AWS credentials with PutObject permission and access to KMS key.
"""
from __future__ import annotations
import argparse
import json
import pathlib
import boto3

DEFAULT_BUCKET = "autorescue-personal-info"
DEFAULT_KEY = "personal_info.json"

def upload(file: str, bucket: str, key: str, profile: str | None = None):
    path = pathlib.Path(file)
    if not path.is_file():
        raise SystemExit(f"File not found: {file}")
    data = path.read_bytes()
    # Rudimentary validation - ensure JSON parses
    try:
        parsed = json.loads(data)
    except Exception as e:
        raise SystemExit(f"Invalid JSON: {e}")
    if profile:
        session = boto3.Session(profile_name=profile)
        s3 = session.client("s3")
    else:
        s3 = boto3.client("s3")
    s3.put_object(
        Bucket=bucket,
        Key=key,
        Body=json.dumps(parsed, separators=(",", ":")),  # minify before upload
        ContentType="application/json",
        ServerSideEncryption="aws:kms",
    )
    print(f"Uploaded {file} to s3://{bucket}/{key} ({len(data)} bytes -> {len(json.dumps(parsed))} bytes)")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Upload personal_info.json to S3")
    parser.add_argument("--file", required=True, help="Path to local personal_info.json")
    parser.add_argument("--bucket", default=DEFAULT_BUCKET)
    parser.add_argument("--key", default=DEFAULT_KEY)
    parser.add_argument("--profile", help="AWS profile name (e.g. SBPOC11)")
    args = parser.parse_args()
    upload(args.file, args.bucket, args.key, args.profile)
