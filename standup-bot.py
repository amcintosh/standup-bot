from __future__ import print_function
from flask import Flask, request

app = Flask(__name__)


@app.route("/", methods=['POST'])
def command():
    # ignore message we sent
    user_name = request.form.get("user_name", "").strip()
    print(user_name)
    print("stuff happened")


@app.route("/")
def status():
    return 'Hello World!'
