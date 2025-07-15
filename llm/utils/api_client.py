import json
import requests

from http import HTTPStatus
from requests.exceptions import RequestException
from utils.logger import logger
from utils.common import (
    Env
)
from utils.exceptions import (
    SendAssistantMessageException,
)
from utils.oauth import generate_oauth_token

AUTH0_OAUTH_URL = Env.AUTH0_OAUTH_URL
AUTH0_OAUTH_HEADERS = {"content-type": "application/json"}


class AssistantSendMessageException(Exception):
    def __init__(self, message="Unexcpected error sending message to assistant"):
        self.message = message
        self.code = 500


class AssistantClient:
    domain = Env.AUTH0_ASSISTANT_AUDIENCE

    def __init__(self, **kwargs):
        self.correlation_id = kwargs.get("correlation_id")
        self.headers = self._generate_headers()

    def _generate_headers(self):
        oauth_token = generate_oauth_token(
            Env.AUTH0_ASSISTANT_CLIENT_ID,
            Env.AUTH0_ASSISTANT_CLIENT_SECRET,
            Env.AUTH0_ASSISTANT_AUDIENCE,
        )
        return {
            "Content-Type": "application/json",
            "x-correlation-id": self.correlation_id,
            "x-api-key": Env.ASSISTANT_API_KEY,
            "Authorization": f"Bearer {oauth_token}",
        }

    def send_message(self, message: str, channel: str):
        endpoint = "/notifications"
        payload = {
            "message": message,
            "webhook_channel": channel,
        }

        try:
            resp = requests.post(
                f"{self.domain}{endpoint}",
                headers=self.headers,
                json=payload,
                timeout=5,
            )
        except RequestException as e:
            raise AssistantSendMessageException(str(e))

        return resp.json()


def notify_assistant(correlation_id, message):
    assistant_client = AssistantClient(correlation_id=correlation_id)

    try:
        assistant_client.send_message(message=message, channel="general")
    except SendAssistantMessageException as e:
        logger.error(
            "SEND_ASSISTANT_MESSAGE_EXCEPTION",
            message="Could not send message to assistant",
            error=str(e),
        )
        raise e
