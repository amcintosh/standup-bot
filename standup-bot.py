from __future__ import print_function
import json
import logging
import os
import random
import re
from flask import Flask, request
from imgurpython import ImgurClient
from slacker import Slacker

app = Flask(__name__)

slack_client = Slacker(os.getenv('SLACK_TOKEN'))
slack_username = os.getenv('SLACK_USERNAME', 'Standup-bot')
slack_channel = os.getenv('SLACK_CHANNEL')
slack_message = os.getenv("SLACK_MESSAGE", "Shall we standup?")

imgur_album_id = os.getenv("IMGUR_ALBUM_ID")
imgur_client = ImgurClient(
    os.getenv("IMGUR_CLIENT_ID"),
    os.getenv("IMGUR_CLIENT_SECRET")
)

log = logging.getLogger(__name__)
logging.basicConfig(format='%(asctime)s - %(levelname)s: %(message)s')
if (os.getenv("DEBUG", False) in ["true", "True", "Yes", "yes"]):
    log.setLevel(logging.DEBUG)


def post_message(text, attachments=[]):
    log.debug("Sending message: %s, %s", text, attachments)
    slack_client.chat.post_message(
        channel=slack_channel,
        text=text,
        username=slack_username,
        parse="full",
        link_names=1,
        attachments=attachments)


def get_image_attachment():
    items = imgur_client.get_album_images(imgur_album_id)
    if len(items) < 1:
        return None
    item = random.choice(items)
    attachments = [{
            'fallback': "Standup!",
            'title': "Standup!",
            'title_link': "Standup!",
            'image_url': item.link
        }]
    return attachments


def post_standup():
    message = "<!here>: %s" % slack_message
    post_message(message, get_image_attachment())


@app.route("/", methods=['POST'])
def command():
    # ignore message we sent
    incoming_text = request.form.get("text", "").strip().lower()

    # find !command, but ignore <!command
    pattern = re.compile("(!standup)( [a-zA-Z ]+)?")
    match = pattern.findall(incoming_text, 0)[0]

    if not match or match[0] != "!standup":
        log.debug("No match: %s", incoming_text)
        return

    if not match[1]:
        log.debug("Basic Standup")
        post_standup()
    elif match[1].strip() == "help":
        # help
        pass
    elif match[1].strip() == "delay":
        # delay
        # return json.dumps({ })
        pass
    else:
        log.debug("No command: %s", incoming_text)
    return json.dumps({})


@app.route("/")
def status():
    return "%s is running." % __name__
