import os
import json
import io
import boto3
import botocore
import time
import bcrypt
from typing import Dict, Any, Optional
import streamlit as st

# Expected env vars (or set via Streamlit secrets):
# S3_BUCKET, S3_KEY, AWS_REGION (optional if role provides it)
S3_BUCKET = os.getenv("S3_BUCKET") or st.secrets.get("S3_BUCKET")
S3_KEY = os.getenv("S3_KEY") or st.secrets.get("S3_KEY")
AWS_REGION = os.getenv("AWS_REGION") or st.secrets.get("AWS_REGION")

if not S3_BUCKET or not S3_KEY:
    raise RuntimeError("S3_BUCKET and S3_KEY must be set via env or st.secrets")

_session = boto3.session.Session(region_name=AWS_REGION) if AWS_REGION else boto3.session.Session()
_s3 = _session.client("s3")

@st.cache_data(show_spinner=False, ttl=60)  # refresh once a minute
def _fetch_users_from_s3(etag_hint: Optional[str] = None) -> Dict[str, Any]:
    """
    Downloads users.json from S3 and returns:
    {
      'users_by_name': { 'alice': {'password_hash': '...', 'roles': [...]}, ... },
      'etag': '...'
    }
    """
    # Light conditional download using If-None-Match when possible
    kwargs = {"Bucket": S3_BUCKET, "Key": S3_KEY}
    if etag_hint:
        kwargs["IfNoneMatch"] = etag_hint

    try:
        obj = _s3.get_object(**kwargs)
        body = obj["Body"].read()
        etag = obj.get("ETag", "").strip('"')
        data = json.loads(body.decode("utf-8"))
        users_by_name = {
            u["username"]: {"password_hash": u["password_hash"], "roles": u.get("roles", [])}
            for u in data.get("users", [])
        }
        return {"users_by_name": users_by_name, "etag": etag, "fetched_at": int(time.time())}
    except botocore.exceptions.ClientError as e:
        # 304 Not Modified path isn't available via get_object; if-None-match leads to PreconditionFailed in some flows.
        # To keep this simple/robust, just re-download on ttl expiry. If you prefer strong conditional requests,
        # switch to HEAD + compare ETag before GET.
        raise e

def verify_credentials(username: str, password: str) -> bool:
    """
    Returns True if username exists and password matches bcrypt hash.
    """
    cache = _fetch_users_from_s3()  # cached for TTL
    user = cache["users_by_name"].get(username)
    if not user:
        return False
    stored_hash = user["password_hash"].encode("utf-8")
    return bcrypt.checkpw(password.encode("utf-8"), stored_hash)


def get_user_roles(username: str):
    cache = _fetch_users_from_s3()
    user = cache["users_by_name"].get(username)
    return user.get("roles", []) if user else []
