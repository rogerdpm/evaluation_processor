from dotenv import load_dotenv
import os
from pathlib import Path
from enum import Enum
from typing import Any, Dict
import requests
import json
import time
from http import HTTPStatus
from requests.exceptions import HTTPError
import logging
from worker.core.config import settings

# Configure logger
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


# dotenv_path = Path('.env')
# load_dotenv(dotenv_path=dotenv_path)

# GENEXT_APP_ID_PROD = os.getenv('GENEXT_APP_ID_PROD')
# GENEXT_API_KEY_PROD= os.getenv('GENEXT_API_KEY_PROD')
# GENEXT_API_SECRET_PROD= os.getenv('GENEXT_API_SECRET_PROD')

# CLIENT_ID_PROD = os.getenv('CLIENT_ID_PROD')
# CLIENT_SECRET_PROD = os.getenv('CLIENT_SECRET_PROD')
# TENANT_ID_PROD = os.getenv('TENANT_ID_PROD')

GENEXT_APP_ID_PROD=str(settings.GENEXT_APP_ID_PROD)
GENEXT_API_KEY_PROD=str(settings.GENEXT_API_KEY_PROD)
GENEXT_API_SECRET_PROD=str(settings.GENEXT_API_SECRET_PROD)

CLIENT_ID_PROD=str(settings.CLIENT_ID_PROD)
CLIENT_SECRET_PROD=str(settings.CLIENT_SECRET_PROD)
TENANT_ID_PROD=str(settings.TENANT_ID_PROD)

CONFIG = {
    "PROD": {
        "HOSTNAME": "api.gcp.cloud.bmw",
        "CLIENT_ID": CLIENT_ID_PROD,
        "CLIENT_SECRET": CLIENT_SECRET_PROD,
        "API_KEY": GENEXT_API_KEY_PROD,
    },
}

ENVIRONMENT = "PROD"
POLLING_INTERVAL = 0.6

API_BASE_PATH = f"https://{CONFIG[ENVIRONMENT]['HOSTNAME']}/generaid/llm/v1"




class LlmApiModel(str, Enum):
    GPT_35_TURBO_16K = "gpt-35-turbo-16k"
    GPT_4_TURBO = "gpt-4-turbo-8k"
    ADA = "text-embedding-ada-v002"
    SONNET = "anthropic.claude-3-sonnet-20240229-v1:0"
    HAIKU = "anthropic.claude-3-haiku-20240307-v1:0"
    GPT_4o = "gpt-4o"


class GenextAPI:
    def __init__(self, question: str, model_name: LlmApiModel = LlmApiModel.HAIKU, temperature: float = 0.0, max_completion_token_count: int = 400, content: str = "You are a friendly AI assistant, helping humans with their questions."):
        self.question = question
        self.model_name = model_name
        self.temperature = temperature
        self.max_completion_token_count = max_completion_token_count
        self.content = content
        self.conversation_id = None  # Added this line
        
        self.payload = self._create_payload()
        
    def _create_payload(self) -> Dict[str, Any]:
        history = [
            {
                "role": "system",
                "content": self.content,
            },
            {"role": "user", "content": self.question},
        ]
        payload = {
            "model_name": self.model_name,
            "model_parameters": {
                "temperature": self.temperature,
                "max_completion_token_count": self.max_completion_token_count
            },
            "history": history,
        }
        if self.conversation_id != None:
            payload["conversation_id"] = self.conversation_id
        return payload
        
    def _create_multimodal_payload(self):
        multimodal_payload = {
        "model_name": self.model_name,
        "model_parameters": {"temperature": self.temperature, "max_completion_token_count": self.max_completion_token_count},
        "history": [
            {
                "role": "system",
                "content": self.content,
            },
            #{"role": "assistant", "content": "Hello, how can I help you?"},
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": self.question},
                    {
                        "type": "image",
                        "source": {
                            "type": "base64",
                            "media_type": "image/jpeg",
                            "data": "YOUR IMAGE IN BASE64",
                        },
                    },
                ],
            },
        ],
        }
        if self.conversation_id != None:
            multimodal_payload["conversation_id"] = self.conversation_id
        return multimodal_payload

    @staticmethod
    def load_and_get_bmw_ca() -> str:
        ca_path = os.path.abspath(
            # f"{os.path.dirname(__file__)}/../../certificate/BMW_Trusted_Certificates_Latest.pem"
            f"{os.path.dirname(__file__)}/BMW_Trusted_Certificates_Latest.pem"
        )
        if not os.path.exists(ca_path):
            logger.info(f"CA file does not exist yet, trying to download into {ca_path}")
            response = requests.get(
                "http://sslcrl.bmwgroup.com/pki/BMW_Trusted_Certificates_Latest.pem"
            )
            response.raise_for_status()
            with open(ca_path, "wb") as f:
                f.write(response.content)
        return ca_path

    @staticmethod
    def get_webeam_access_token(requests_session: requests.Session) -> str:
        auth_endpoint = f"https://{'auth' if ENVIRONMENT == 'PROD' else 'auth-i'}.bmwgroup.net/auth/oauth2/realms/root/realms/machine2machine/access_token"
        auth_response = requests_session.post(
            auth_endpoint,
            headers={"Content-Type": "application/x-www-form-urlencoded"},
            data={
                "grant_type": "client_credentials",
                "client_id": CONFIG[ENVIRONMENT]["CLIENT_ID"],
                "client_secret": CONFIG[ENVIRONMENT]["CLIENT_SECRET"],
                "scope": "machine2machine",
            },
        )
        if auth_response.status_code != HTTPStatus.OK:
            raise Exception(
                f"OAuth2 authentication failed. HTTP status code: {auth_response.status_code}."
            )
        else:
            access_token = auth_response.json().get("access_token")
            logger.info("Successfully received WEN token.")
            return access_token

    def get_generate_chat_request(self, requests_session: requests.Session, request_id: str) -> Any:
        response = requests_session.get(
            f"{API_BASE_PATH}/tenant_id/text-prediction/generate-chat-request/{request_id}"
        )
        return response.json()

    @staticmethod
    def post_generate_chat_request(requests_session: requests.Session, payload: Any) -> str:
        response = requests_session.post(
            f"{API_BASE_PATH}/tenant_id/text-prediction/generate-chat-request",
            json=payload,
        )
        return response.json()["request_id"]

    def poll_get_generate_chat_request(self, requests_session: requests.Session, request_id: str):
        logger.info(f"Start polling for request with ID {request_id}")
        start_time = time.time()
        count = 0
        while count < 50:
            response = self.get_generate_chat_request(requests_session, request_id)
            if response["status"] != "PENDING":
                duration = time.time() - start_time
                logger.info(f"Finished polling after {duration:.2f} seconds.")
                self.conversation_id = response.get("conversation_id")  # Added this line
                return response
            time.sleep(POLLING_INTERVAL)
        raise Exception("Polling took too long, aborting")
    
    def post_generate_embedding_request(self, requests_session: requests.Session, input_text: str) -> str:
        payload = {
            "model_name": "text-embedding-ada-v002",
            "input": input_text
        }
        response = requests_session.post(
            f"{API_BASE_PATH}/tenant_id/embedding/generate-embedding-request",
            json=payload,
        )
        return response.json()["request_id"]

    def get_generate_embedding_request(self, requests_session: requests.Session, request_id: str) -> Any:
        response = requests_session.get(
            f"{API_BASE_PATH}/tenant_id/embedding/generate-embedding-request/{request_id}"
        )
        return response.json()

    def poll_generate_embedding_request(self, requests_session: requests.Session, request_id: str):
        logger.info(f"Start polling for embedding request with ID {request_id}")
        start_time = time.time()
        count = 0
        while count < 50:
            response = self.get_generate_embedding_request(requests_session, request_id)
            if response["status"] != "PENDING":
                duration = time.time() - start_time
                logger.info(f"Finished polling after {duration:.2f} seconds.")
                return response
            time.sleep(1)  # Wait at least 1 second between polls
        raise Exception("Polling took too long, aborting")

    def generate_embedding(self, input_text: str) -> Any:
        try:
            with requests.Session() as requests_session:
                requests_session.verify = self.load_and_get_bmw_ca()
                requests_session.trust_env = False
                requests_session.proxies = {"http": "", "https": ""}
                requests_session.hooks = {
                    "response": lambda r, *args, **kwargs: r.raise_for_status()
                }

                wen_token = self.get_webeam_access_token(requests_session)
                requests_session.headers.update(
                    {
                        "Accept": "application/json",
                        "x-apikey": CONFIG[ENVIRONMENT]["API_KEY"],
                        "Authorization": f"Bearer {wen_token}",
                    }
                )

                request_id = self.post_generate_embedding_request(requests_session, input_text)
                embedding_response = self.poll_generate_embedding_request(requests_session, request_id)
                #print(embedding_response)
                logger.info("Received embedding response.")
                return embedding_response
        except HTTPError as e:
                logger.exception(f"Error with embedding request:\n{e.response.json()}")	

    def run(self, use_m2m=False, m2m_token=""):
        try:
            with requests.Session() as requests_session:
                requests_session.verify = self.load_and_get_bmw_ca()
                requests_session.trust_env = False
                requests_session.proxies = {"http": "", "https": ""}
                requests_session.hooks = {
                    "response": lambda r, *args, **kwargs: r.raise_for_status()
                }

                if use_m2m:
                    wen_token = m2m_token
                else:
                    wen_token = self.get_webeam_access_token(requests_session)

                requests_session.headers.update(
                    {
                        "Accept": "application/json",
                        "x-apikey": CONFIG[ENVIRONMENT]["API_KEY"],
                        "Authorization": f"Bearer {wen_token}",
                    }
                )

                request_id = self.post_generate_chat_request(requests_session, self.payload)
                answer = self.poll_get_generate_chat_request(requests_session, request_id)
                logger.info(f"Received answer.")
                return answer
        except HTTPError as e:
            logger.exception(f"Error with request:\n{e.response.json()}")