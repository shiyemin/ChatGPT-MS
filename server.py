"""Make some requests to OpenAI's chatbot"""

import os
import time
import json
import threading
from expiringdict import ExpiringDict

from flask import Flask, request, jsonify, Response

from Classes import auth as Auth
from PyChatGPT.Classes import chat as Chat

# Fancy stuff
import colorama
from colorama import Fore


MAX_SESSION_NUM = 3000
MAX_AGE_SECONDS = 1800

APP = Flask(__name__)

colorama.init(autoreset=True)

# Check if config.json exists
if not os.path.exists("config.json"):
    print(">> config.json is missing. Please create it.")
    print(f"{Fore.RED}>> Exiting...")
    exit(1)

with open("config.json", "r") as f:
    config = json.load(f)
    # Check if email & password are in config.json
    if "email" not in config or "password" not in config:
        print(">> config.json is missing email or password. Please add them.")
        print(f"{Fore.RED}>> Exiting...")
        exit(1)

# Try login
sem = threading.Semaphore()
access_token = None
def try_login():
    global access_token
    sem.acquire()
    if Auth.expired_creds():
        open_ai_auth = Auth.LocalOpenAIAuth(email_address=config["email"], password=config["password"])
        print(f"{Fore.GREEN}>> Credentials have been refreshed.")
        open_ai_auth.begin()
        time.sleep(3)
        access_token = Auth.get_access_token()
    sem.release()

print(f"{Fore.GREEN}>> Checking if credentials are expired...")
if Auth.expired_creds():
    print(f"{Fore.RED}>> Your credentials are expired." + f" {Fore.GREEN}Attempting to refresh them...")
    try_login()
    is_still_expired = Auth.expired_creds()
    if is_still_expired:
        print(f"{Fore.RED}>> Failed to refresh credentials. Please try again.")
        exit(1)
    else:
        print(f"{Fore.GREEN}>> Successfully refreshed credentials.")
else:
    print(f"{Fore.GREEN}>> Your credentials are valid.")
    access_token = Auth.get_access_token()

# Cache all conv id
prev_conv_id_cache = ExpiringDict(max_len=MAX_SESSION_NUM, max_age_seconds=MAX_AGE_SECONDS)
def get_prev_conv_id(user):
    if user not in prev_conv_id_cache:
        prev_conv_id_cache[user] = None
    prev_conv_id = prev_conv_id_cache[user]
    return prev_conv_id

def set_prev_conv_id(user, prev_conv_id):
    prev_conv_id_cache[user] = prev_conv_id


@APP.route("/chat", methods=["POST"])
def chat():
    global access_token

    message = request.json["message"].strip()
    user = request.json["user"].strip()
    prev_conv_id = get_prev_conv_id(user)
    print(f"{user} message: {message}")
    answer, previous_convo = Chat.ask(auth_token=access_token,
                                      prompt=message,
                                      previous_convo_id=prev_conv_id)
    if answer == "400" or answer == "401":
        print(f"{Fore.RED}>> Your token is invalid. Attempting to refresh..")
        try_login()
        return Response(
                "Please try again.",
                status=400,
            )

    print(f"Response to {user}: {answer}")
    if previous_convo is not None:
        set_prev_conv_id(user, previous_convo)
    return jsonify({"response": answer}), 200

def start_browser():
    APP.run(port=5000, threaded=True)

if __name__ == "__main__":
    start_browser()
