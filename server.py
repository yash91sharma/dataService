from flask import Flask, jsonify
from apscheduler.schedulers.background import BackgroundScheduler
from src.generate_daily_snapshot import generate_daily_snapshot
from waitress import serve

app = Flask(__name__)

scheduler = BackgroundScheduler({"apscheduler.timezone": "US/Pacific"})
# scheduler.add_job(your_function, 'cron', hour=18, minute=0)
scheduler.add_job(generate_daily_snapshot, "interval", seconds=10)
scheduler.start()


@app.route("/")
def hello():
    return jsonify({"message": "Portfolio Data Service is up!"})


if __name__ == "__main__":
    # dev server
    app.run(debug=True, port=12345)
    # serve(app, host="0.0.0.0", port = 12345)
