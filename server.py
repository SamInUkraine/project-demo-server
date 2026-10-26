import os
import json
import urllib.request
import time
from flask import Flask, render_template, request
from flask_socketio import SocketIO, emit, join_room


MAX_TEXT = 300
MAX_HISTORY = 600

visitors = {}
counter = {"n": 0}


app = Flask(__name__)
app.config["SECRET_KEY"] = "demo-privacy"
socketio = SocketIO(app, cors_allowed_origins="*")

COLORS = [("red", "червоний"), ("blue", "синій"), ("green", "зелений"),
          ("orange", "помаранчевий"), ("purple", "фіолетовий"),
          ("brown", "коричневий"), ("magenta", "малиновий"),
          ("teal", "бірюзовий")]


def public(sid, v):
    return {"id": sid, "num": v["num"],
            "color": v["color"],
            "device": v["device"], "ip": v.get("ip", ""),
            "geo": v.get("geo", {}),                        # ← додали
            "text": v["text"], "submitted": v["submitted"]}

            
def client_ip():
    # На Render справжній IP — у заголовку X-Forwarded-For (перший у списку).
    fwd = request.headers.get("X-Forwarded-For", "")
    if fwd:
        return fwd.split(",")[0].strip()
    return request.remote_addr or "невідомо"


geo_cache = {}   # ip -> {city, country, isp}, щоб не питати двічі про той самий IP

def ip_geo(ip):
    if ip in geo_cache:
        return geo_cache[ip]
    result = {"city": "", "country": "", "isp": ""}
    try:
        url = "http://ip-api.com/json/" + ip + "?fields=status,city,country,isp"
        with urllib.request.urlopen(url, timeout=2) as r:
            d = json.load(r)
        if d.get("status") == "success":
            result = {"city": d.get("city", ""),
                      "country": d.get("country", ""),
                      "isp": d.get("isp", "")}
    except Exception:
        pass
    geo_cache[ip] = result
    return result


@app.route("/")
def index():
    return render_template("phone.html")

@app.route("/panel")
def panel():
    return render_template("panel.html")


@socketio.on("hello_phone")
def hello_phone(data):
    """Телефон приєднується ПІСЛЯ згоди. data містить інфо про пристрій."""
    if request.sid in visitors:
        return
    counter["n"] += 1
    n = counter["n"]
    color, colorname = COLORS[(n - 1) % len(COLORS)]
    ip = client_ip()
    geo = ip_geo(ip)
    visitors[request.sid] = {
        "num": n, "color": color, "colorname": colorname,
        "device": data.get("device", {}),
        "ip": ip,
        "geo": geo,                             # ← додали
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


@socketio.on("hello_panel")
def hello_panel():
    join_room("panel")
    emit("state", [public(s, v) for s, v in visitors.items()])


@socketio.on("disconnect")
def on_disconnect():
    if visitors.pop(request.sid, None):
        emit("visitor_leave", {"id": request.sid}, to="panel")


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000)) # Якщо щось піде не так з хостингом, панель запуститься локально
    print("Панель для проектора:  http://localhost:%d/panel" % port)
    print("Сторінка для телефонів: http://<твій-IP>:%d/" % port)
    socketio.run(app, host="0.0.0.0", port=port, debug=False,
                 allow_unsafe_werkzeug=True)
