from flask import Flask, jsonify, request
from waitress import serve
from src.generate_daily_snapshots import generate_daily_snapshots
import logging

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S %p %Z",
)
app = Flask(__name__)


@app.route("/")
def hello():
    return jsonify({"message": "Portfolio Data Service is up!"})

@app.route("/generateDailySnapshots", methods=["POST"])
def generate_daily_snapshots_route():
    return generate_daily_snapshots(request)


if __name__ == "__main__":
    # dev server
    # app.run(debug=True, port=12345)
    serve(app, host="127.0.0.1", port = 12345)
