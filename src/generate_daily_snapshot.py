import json
from flask import jsonify
from .utils import GET_TXN_BY_PORTFOLIO_DATE_URL
import requests


def extract_snapshot_from_response(data):
    row = data["rows"][0]
    # print(row)
    snapshot = {}
    snapshot["portfolio_value"] = row.get("portfolio_value")
    snapshot["snapshot_date"] = row.get("snapshot_date")
    snapshot["assets"] = []
    for asset in json.loads(row.get("assets")):
        snapshot["assets"].append(asset)
    return snapshot


def generate_daily_snapshot():
    portfolio_id = "p1"
    try:
        response = requests.request(
            method="get",
            url=GET_TXN_BY_PORTFOLIO_DATE_URL,
            headers={"Content-Type": "application/json"},
            json={"portfolio_id": portfolio_id},
        )
        response.raise_for_status()
        # add fields validation
        latest_snapshot = extract_snapshot_from_response(response.json())
        return latest_snapshot
    except Exception as e:
        return jsonify({"error": str(e)}), 500
