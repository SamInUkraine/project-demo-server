import os
import time
from flask import Flask, render_template, request
from flask_socketio import SocketIO, emit, join_room


app = Flask(__name__)
app.config["SECRET_KEY"] = "demo-privacy"
socketio = SocketIO(app, cors_allowed_origins="*")


MAX_TEXT = 300
MAX_HISTORY = 600

visitors = {}        
counter = {"n": 0}

def public(sid, v):
    return {"id": sid, "num": v["num"],
            "color": v["color"], "colorname": v["colorname"],
            "device": v["device"], "text": v["text"],
            "submitted": v["submitted"]}

