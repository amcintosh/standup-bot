import datetime
import json
import logging
import os
import random
import re
import click
from flask import Flask, request
from imgurpython import ImgurClient
from imgurpython.helpers.error import ImgurClientError
import redis
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

redis_client = redis.from_url(os.getenv("REDIS_URL"))


log = logging.getLogger(__name__)
logging.basicConfig(format='%(asctime)s - %(levelname)s: %(message)s')
if (os.getenv("DEBUG", False) in ["true", "True", "Yes", "yes"]):
    log.setLevel(logging.DEBUG)


def post_message(text, attachments=None):
    if attachments is None:
        attachments = []
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


def before_scheduled_time():
    time_strings = os.getenv('STANDUP_TIME', "").split()
    if len(time_strings) != 2:
        return False
    scheduled_time = datetime.time(time_strings[0], time_strings[1])
    if datetime.now().time() < scheduled_time:
        return True
    return False


def post_standup():
    message = "@channel: %s" % slack_message
    attachment = None
    try:
        attachment = get_image_attachment()
    except ImgurClientError as e:
        log.info("Imgur error", e)
    post_message(message, attachment)


@app.route("/", methods=['POST'])
def api_command():
    incoming_text = request.form.get("text", "").strip().lower()

    pattern = re.compile("(!standup)( [a-zA-Z ]+)?")
    match = pattern.findall(incoming_text, 0)[0]

    if not match or match[0] != "!standup":
        log.debug("No match: %s", incoming_text)
        return

    if not match[1]:
        log.debug("Basic Standup")
        if before_scheduled_time():
            redis_client.set("ignore", True)
        elif redis_client.get("ignore"):
            redis_client.set("ignore", False)
        post_standup()
    elif match[1].strip() == "delay":
        redis_client.set("ignore", True)
    elif match[1].strip() == "help":
        message = "Standup bot commands:\n" \
            "`!standup` - Call for standup, resetting any delay\n" \
            "`!standup delay` - Prevent the next scheduled standup message until manually called."
        post_message(message)

    else:
        # Shouldn't get here (famous last words).
        log.debug("No command: %s", incoming_text)
    return json.dumps({})


@app.route("/")
def status():
    return "%s is running." % __name__


@click.command()
def cmd_command():
    log.debug("Scheduled standup")
    if datetime.date.today().isoweekday() not in range(1, 6):
        log.debug("No standup: Weekend")
    elif redis_client.get("ignore") == "False":
        log.debug("No standup: Delayed")
    else:
        post_standup()
    redis_client.delete("ignore")

if __name__ == '__main__':
    cmd_command()
