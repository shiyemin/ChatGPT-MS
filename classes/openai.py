# Builtins
import os
import json
import time
import uuid
from typing import Tuple

# Requests
import requests

# Fancy stuff
import colorama
from colorama import Fore

colorama.init(autoreset=True)

from PyChatGPT.src.pychatgpt.classes import openai as OpenAI


def get_access_token():
    """
        Get the access token
        returns:
            str: The access token
    """
    try:
        # Get path using os, it's in ./Classes/auth.json
        path = os.path.dirname(os.path.abspath(__file__))
        path = os.path.join(path, "auth.json")

        with open(path, 'r') as f:
            creds = json.load(f)
            return creds['access_token'], creds['expires_at']
    except FileNotFoundError:
        return None, None


class LocalOpenAIAuth(OpenAI.Auth):

    @staticmethod
    def save_access_token(access_token: str, expiry: int or None = None):
        """
        Save access_token and an hour from now on CHATGPT_ACCESS_TOKEN CHATGPT_ACCESS_TOKEN_EXPIRY environment variables
        :param expiry:
        :param access_token:
        :return:
        """
        try:
            print(f"{Fore.GREEN}[OpenAI][9] {Fore.WHITE}Saving access token...")
            expiry = expiry or int(time.time()) + 3600

            # Get path using os, it's in ./classes/auth.json
            path = os.path.dirname(os.path.abspath(__file__))
            path = os.path.join(path, "auth.json")
            with open(path, "w") as f:
                f.write(json.dumps({"access_token": access_token, "expires_at": expiry}))

            print(f"{Fore.GREEN}[OpenAI][8] {Fore.WHITE}Saved access token")
        except Exception as e:
            raise e


def ask_stream(
        auth_token: Tuple,
        prompt: str,
        conversation_id:
        str or None,
        previous_convo_id: str or None,
        proxies: str or dict or None
) -> Tuple[str, str or None, str or None]:
    auth_token, expiry = auth_token

    headers = {
        'Content-Type': 'application/json',
        'Authorization': f'Bearer {auth_token}',
        'Accept': 'text/event-stream',
        'Referer': 'https://chat.openai.com/chat',
        'Origin': 'https://chat.openai.com',
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/16.1 Safari/605.1.15',
        'X-OpenAI-Assistant-App-Id': ''
    }
    if previous_convo_id is None:
        previous_convo_id = str(uuid.uuid4())

    data = {
        "action": "next",
        "messages": [
            {
                "id": str(uuid.uuid4()),
                "role": "user",
                "content": {"content_type": "text", "parts": [prompt]}
            }
        ],
        "conversation_id": conversation_id,
        "parent_message_id": previous_convo_id,
        "model": "text-davinci-002-render"
    }
    response = requests.post("https://chat.openai.com/backend-api/conversation",
                             headers=headers, data=json.dumps(data), stream=True, timeout=50)
    for line in response.iter_lines():
        try:
            line = line.decode('utf-8')
            if line == "":
                continue
            line = line[6:]
            line = json.loads(line)
            try:
                message = line["message"]["content"]["parts"][0]
                previous_convo = line["message"]["id"]
                conversation_id = line["conversation_id"]
            except:
                continue
            yield message, previous_convo, conversation_id
        except:
            continue
