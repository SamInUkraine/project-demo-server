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
            "device": v["device"], "text": v["text"]}

@app.route("/")    
def index():
    return render_template("phone.html")


@app.route("/panel")
def panel():
    return render_template("panel.html")



@socketio.on("hello_phone")
def hello_phone(data):

    if request.sid in visitors:
        return
    counter["n"] += 1
    n = counter["n"]
    color = COLORS[(n - 1) % len(COLORS)]

    visitors[request.sid] = {
        "num": n, "color": color,
        "device": data.get("device", {}),
        "text": "", "history": [], "submitted": None,
    }
    emit("visitor_join", public(request.sid, visitors[request.sid]), to="panel")
    emit("you_are", {"num": n})



@socketio.on("typing")
def on_typing(data):
    v = visitors.get(request.sid)
    if not v:
        return
    text = str(data.get("text", ""))[:MAX_TEXT]
    v["text"] = text
    v["history"].append({"t": time.time(), "text": text})
    if len(v["history"]) > MAX_HISTORY:
        v["history"].pop(0)
    emit("typing", {"id": request.sid, "text": text}, to="panel")


@socketio.on("touch")
def on_touch(data):
    v = visitors.get(request.sid)
    if not v:
        return
    emit("touch", {"id": request.sid, "color": v["color"],
                   "x": data.get("x", 0), "y": data.get("y", 0),
                   "down": data.get("down", False)}, to="panel")

