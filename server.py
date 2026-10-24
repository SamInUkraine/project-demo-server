import os
import time
from flask import Flask, render_template, request
from flask.socketio import SocketIO, emit, join_room


app = Flask(__name__)
app.config["SECRET_KEY"] = "demo-privacy"
socketio = SocketIO(app, cors_allowed_origins="*")


MAX_TEXT = 300
MAX_HISTORY = 600

visitors = {}        
counter = {"n": 0}
