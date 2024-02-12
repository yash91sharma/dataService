from flask import Flask, jsonify
from apscheduler.schedulers.background import BackgroundScheduler
from src.generate_daily_snapshot import generate_daily_snapshot

app = Flask(__name__)

scheduler = BackgroundScheduler()
# scheduler.add_job(your_function, 'cron', hour=18, minute=0)
scheduler.add_job(generate_daily_snapshot, 'interval', seconds=10)
scheduler.start()

@app.route("/")
def hello():
    return jsonify({"message": "Server is running!"})

if __name__ == "__main__":
    app.run(debug=True, port=12345)