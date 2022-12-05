"""Make some requests to OpenAI's chatbot"""

import sys
sys.path.append("ChatGPT/src")

import time
import os
from expiringdict import ExpiringDict

from flask import Flask, request, jsonify, Response

from revChatGPT.revChatGPT import Chatbot
from get_auth import get_token


MAX_SESSION_NUM = 300
MAX_AGE_SECONDS = 1800

APP = Flask(__name__)

config = get_token()
if config is None:
    sys.exit(1)

bot_cache = ExpiringDict(max_len=MAX_SESSION_NUM, max_age_seconds=MAX_AGE_SECONDS)

def get_chatbot(user):
    if user not in bot_cache:
        chatbot = Chatbot(config, conversation_id=None)
        if 'session_token' in config:
            chatbot.refresh_session()
        bot_cache[user] = chatbot
    bot = bot_cache[user]
    bot_cache[user] = bot
    return bot

@APP.route("/chat", methods=["POST"])
def chat():
    message = request.json["message"].strip()
    user = request.json["user"].strip()
    print(f"{user} message: {message}")
    try:
        bot = get_chatbot(user)
        if message == "reset":
            bot.reset_chat()
            response = "done"
        else:
            response = bot.get_chat_response(message, output="text")
            if isinstance(response, Exception):
                raise response
            response = response["message"]
    except Exception as e:
        print(f"Error: ", e)
        return Response(
                str(e),
                status=400,
            )
    print(f"Response to {user}: {response}")
    return jsonify({"response": response}), 200

def start_browser():
    APP.run(port=5000, threaded=True)

if __name__ == "__main__":
    start_browser()
