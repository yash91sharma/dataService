import json
from .utils import (
    GET_SNAPSHOT_BY_PORTFOLIO_DATE_URL,
    validate_fields,
    SNAPSHOT_REQUIRED_FIELDS,
    generate_missing_field_error,
    SNAPSHOT_ASSETS_REQUIRED_FIELDS,
    GET_TXNS_BY_PORTFOLIO_DATE_URL,
    TXNS_REQUIRED_FIELDS,
)
import requests
from datetime import datetime


def convert_snapshot_to_map(data):
    row = data["rows"][0]
    snapshot = {
        "portfolio_value": row.get("portfolio_value"),
        "snapshot_date": row.get("snapshot_date"),
        "snapshot_date": row.get("snapshot_date"),
        "assets": {"cash": 0, "stock": {}, "option": []},
    }
    for asset in json.loads(row.get("assets")):
        if asset.get("entity_type") == "cash":
            snapshot["assets"]["cash"] = asset.get("value")
        elif asset.get("entity_type") == "stock":
            # order is value, qty, cost_basis
            snapshot["assets"]["stock"][asset.get("ticker")] = [
                asset.get("value"),
                asset.get("qty"),
                asset.get("cost_basis"),
            ]
        elif asset.get("entity_type") in ["option-put", "option-call"]:
            snapshot["assets"]["option"].append(asset)
    return snapshot


def validate_snapshot(data, fields, subfields):
    if "rows" not in data:
        return generate_missing_field_error("rows")
    if len(data["rows"]) != 1:
        return f'Snapshot has incorrect number of rows, expected 1, got {len(data["rows"])}.'
    row = data["rows"][0]
    basic_field_validation_error = validate_fields(row, fields)
    if basic_field_validation_error is not None:
        return basic_field_validation_error
    assets_field_validation_error = validate_fields(row.get("assets"), subfields)
    if assets_field_validation_error is not None:
        return assets_field_validation_error
    return None


def validate_txns(data, fields):
    if "rows" not in data:
        return generate_missing_field_error("rows")
    if len(data["rows"]) > 0:
        for row in data["rows"]:
            basic_field_validation_error = validate_fields(row, fields)
            if basic_field_validation_error is not None:
                return basic_field_validation_error
    return None


def get_latest_snapshot_map(portfolio_id):
    try:
        response = requests.request(
            method="get",
            url=GET_SNAPSHOT_BY_PORTFOLIO_DATE_URL,
            headers={"Content-Type": "application/json"},
            json={"portfolio_id": portfolio_id},
        )
        response.raise_for_status()
        snapshot_validation_error = validate_snapshot(
            response.json(), SNAPSHOT_REQUIRED_FIELDS, SNAPSHOT_ASSETS_REQUIRED_FIELDS
        )
        if snapshot_validation_error is not None:
            raise Exception(snapshot_validation_error)
        return convert_snapshot_to_map(response.json())
    except Exception as e:
        print("Error occured while generating daily snapshot: ", e)
        return e


def get_all_transactions(portfolio_id, start_date, end_date):
    try:
        response = requests.request(
            method="get",
            url=GET_TXNS_BY_PORTFOLIO_DATE_URL,
            headers={"Content-Type": "application/json"},
            json={
                "portfolio_id": portfolio_id,
                "start_date": start_date,
                "end_date": end_date,
            },
        )
        response.raise_for_status()
        transactions_validation_error = validate_txns(
            response.json(), TXNS_REQUIRED_FIELDS
        )
        if transactions_validation_error is not None:
            raise Exception(transactions_validation_error)
        # print("yo \n",response.json())
        return True
    except Exception as e:
        print("Error occured while generating daily snapshot: ", e)
        return e


def generate_daily_snapshot():
    portfolio_id = "p1"
    snapshot_map = get_latest_snapshot_map(portfolio_id)
    if isinstance(snapshot_map, Exception):
        return False
    print(snapshot_map)
    today_date = datetime.today().strftime("%Y-%m-%d")
    all_txns = get_all_transactions(
        portfolio_id, snapshot_map.get("snapshot_date"), today_date
    )
    print(all_txns)
    return True
