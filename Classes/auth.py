# Builtins
import os
import json
import time

# Fancy stuff
import colorama
from colorama import Fore

colorama.init(autoreset=True)

from PyChatGPT.Classes import auth as Auth


def expired_creds() -> bool:
    """
        Check if the creds have expired
        returns:
            bool: True if expired, False if not
    """
    try:
        # Get path using os, it's in ./Classes/auth.json
        path = os.path.dirname(os.path.abspath(__file__))
        path = os.path.join(path, "auth.json")

        with open(path, 'r') as f:
            creds = json.load(f)
            expires_at = float(creds['expires_at'])
            if time.time() > expires_at + 3600:
                return True
            else:
                return False
    except FileNotFoundError:
        return True


def get_access_token() -> str:
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
            return creds['access_token']
    except FileNotFoundError:
        return ""


class LocalOpenAIAuth(Auth.OpenAIAuth):

    @staticmethod
    def save_access_token(access_token: str):
        """
        Save access_token and an hour from now on ./Classes/auth.json
        :param access_token:
        :return:
        """
        with open("Classes/auth.json", "w") as f:
            f.write(json.dumps({"access_token": access_token, "expires_at": time.time() + 3600}))
        print(f"{Fore.GREEN}[OpenAI][8] {Fore.WHITE}Saved access token")
