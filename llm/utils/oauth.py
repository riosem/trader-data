import boto3
import requests

from datetime import datetime, timedelta
from utils.common import Env
from utils.logger import logger

CACHE_TTL = 3600 * 12  # 12 hours

dynamodb = boto3.resource("dynamodb", Env.REGION)
cache_table = dynamodb.Table(Env.CACHE_TABLE_NAME)


def get_cached_token(cache_key):
    dynamodb = boto3.resource("dynamodb", Env.REGION)
    cache_table = dynamodb.Table(Env.CACHE_TABLE_NAME)
    try:
        response = cache_table.get_item(Key={"cache_key": cache_key})

        if "Item" in response:
            item = response["Item"]
            expiration = datetime.fromisoformat(item["expiration"])
            if datetime.utcnow() < expiration:
                return item["token"]
    except Exception as e:
        logger.error(
            "GET_CACHE_TOKEN_ERROR", message=f"Error getting cached token: {e}"
        )
    return None


def set_cached_token(cache_key, token, ttl):
    dynamodb = boto3.resource("dynamodb", Env.REGION)
    cache_table = dynamodb.Table(Env.CACHE_TABLE_NAME)
    expiration = (datetime.utcnow() + timedelta(seconds=ttl)).isoformat()
    try:
        cache_table.put_item(
            Item={"cache_key": cache_key, "token": token, "expiration": expiration}
        )
    except Exception as e:
        logger.error(
            "SET_CACHE_TOKEN_ERROR", message=f"Error setting cached token: {e}"
        )


def generate_oauth_token(
    client_id, client_secret, audience, grant_type="client_credentials"
):
    cache_key = f"trader_oauth_token_{client_id}_{audience}"
    cached_token = get_cached_token(cache_key)

    if cached_token:
        return cached_token

    url = Env.AUTH0_OAUTH_URL
    headers = {"content-type": "application/json"}
    payload = {
        "client_id": client_id,
        "client_secret": client_secret,
        "audience": audience,
        "grant_type": grant_type,
    }

    response = requests.post(url, json=payload, headers=headers)
    response.raise_for_status()
    token = response.json().get("access_token")

    # Cache the token with a TTL of 3600 seconds (1 hour)
    set_cached_token(cache_key, token, ttl=CACHE_TTL)
    return token
