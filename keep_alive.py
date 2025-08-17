from flask import Flask
import threading

app = Flask("")

@app.route("/")
def home():
    return "Bot is alive!"

def run_flask_server():
    app.run(host="0.0.0.0", port=8080)
