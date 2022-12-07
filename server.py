"""Make some requests to OpenAI's chatbot"""

import os
import time
import json
import base64
import threading
from expiringdict import ExpiringDict

from flask import Flask, request, jsonify, Response

from classes import openai as OpenAI
from PyChatGPT.src.pychatgpt.classes import chat as Chat

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

# Get access token
access_token = OpenAI.get_access_token()
def access_token_expired():
    if access_token is None or \
            access_token[0] is None or \
            access_token[1] is None or \
            access_token[1] < time.time():
        return True
    return False

# Try login
sem = threading.Semaphore()
def try_login():
    global access_token
    sem.acquire()
    if access_token_expired():
        print(f"{Fore.RED}>> Try to refresh credentials.")
        open_ai_auth = OpenAI.LocalOpenAIAuth(email_address=config["email"], password=config["password"])
        open_ai_auth.create_token()

        # If after creating the token, it's still expired, then something went wrong.
        access_token = OpenAI.get_access_token()
        if access_token_expired():
            print(f"{Fore.RED}>> Failed to refresh credentials. Please try again.")
            exit(1)
        else:
            print(f"{Fore.GREEN}>> Successfully refreshed credentials.")

    sem.release()

if access_token_expired():
    try_login()
else:
    print(f"{Fore.GREEN}>> Your credentials are valid.")

# Cache all conv id
# user => (conversation_id, previous_convo_id)
prev_conv_id_cache = ExpiringDict(max_len=MAX_SESSION_NUM, max_age_seconds=MAX_AGE_SECONDS)
def get_prev_conv_id(user):
    if user not in prev_conv_id_cache:
        prev_conv_id_cache[user] = (None, None)
    conversation_id, prev_conv_id = prev_conv_id_cache[user]
    return conversation_id, prev_conv_id

def set_prev_conv_id(user, conversation_id, prev_conv_id):
    prev_conv_id_cache[user] = (conversation_id, prev_conv_id)


@APP.route("/chat", methods=["POST"])
def chat():
    global access_token

    message = request.json["message"].strip()
    user = request.json["user"].strip()

    if access_token_expired():
        try:
            try_login()
        except:
            return Response("ChatGPT login error", status=400)

    print(f"{Fore.RED}[FROM {user}] >> {message}")
    if message == "reset":
        set_prev_conv_id(user, None, None)
        answer = "done"
    else:
        conversation_id, prev_conv_id = get_prev_conv_id(user)
        answer, previous_convo, convo_id = Chat.ask(auth_token=access_token,
                                          prompt=message,
                                          conversation_id=conversation_id,
                                          previous_convo_id=prev_conv_id,
                                          proxies=None)
        if answer == "400" or answer == "401":
            print(f"{Fore.RED}>> Failed to get a response from the API.")
            return Response(
                    "Please try again latter.",
                    status=400,
                )
        set_prev_conv_id(user, convo_id, previous_convo)

    print(f"{Fore.GREEN}[TO {user}] >> {answer}")
    return jsonify({"response": answer}), 200


def update_id_in_stream(user, **kwargs):
    answer = None
    try:
        for answer, previous_convo, convo_id in OpenAI.ask_stream(**kwargs):
            set_prev_conv_id(user, convo_id, previous_convo)
            yield json.dumps({"response": answer})
    except GeneratorExit:
        pass
    if answer is None:
        answer = "Unknown error."
        yield json.dumps({"response": answer})
    print(f"{Fore.GREEN}[TO {user}] >> {answer}")
    yield json.dumps({"response": "[DONE]"})


@APP.route("/chat-stream", methods=["POST"])
def chat_stream():
    global access_token

    message = request.json["message"].strip()
    user = request.json["user"].strip()

    if access_token_expired():
        try:
            try_login()
        except:
            return Response("ChatGPT login error", status=400)

    print(f"{Fore.RED}[FROM {user}] >> {message}")
    if message == "reset":
        set_prev_conv_id(user, None, None)
        return jsonify({"response": "done"}), 200
    else:
        conversation_id, prev_conv_id = get_prev_conv_id(user)
        return Response(update_id_in_stream(user=user,
                                          auth_token=access_token,
                                          prompt=message,
                                          conversation_id=conversation_id,
                                          previous_convo_id=prev_conv_id,
                                          proxies=None))

def start_browser():
    APP.run(port=5000, threaded=True)

if __name__ == "__main__":
    start_browser()
