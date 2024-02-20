import copy
import json
from .utils import (
    GET_SNAPSHOT_BY_PORTFOLIO_DATE_URL,
    validate_fields,
    SNAPSHOT_REQUIRED_FIELDS,
    generate_missing_field_error,
    SNAPSHOT_ASSETS_REQUIRED_FIELDS,
    GET_TXNS_BY_PORTFOLIO_DATE_URL,
    TXNS_REQUIRED_FIELDS,
    GET_CLOSE_PRICE_BY_TICKER,
)
import requests
from datetime import datetime, timedelta


def convert_snapshot_to_map(data):
    row = data["rows"][0]
    snapshot = {
        "portfolio_value": row.get("portfolio_value"),
        "snapshot_date": row.get("snapshot_date"),
        "snapshot_date": row.get("snapshot_date"),
        "assets": {"cash": 0, "stock": {}, "option": []},
    }
    snapshot["assets"] = json.loads(row.get("assets"))
    return snapshot


def convert_txns_to_map_by_date(data):
    txns_map_by_date = {}
    for row in data:
        date = row.get("date")
        if date in txns_map_by_date:
            txns_map_by_date[date].append(row)
        else:
            txns_map_by_date[date] = [row]
    return txns_map_by_date


def validate_snapshot(data, fields, subfields):
    try:
        if "rows" not in data:
            raise Exception(generate_missing_field_error("rows"))
        if len(data["rows"]) != 1:
            raise Exception(
                f'Snapshot has incorrect number of rows, expected 1, got {len(data["rows"])}.'
            )
        row = data["rows"][0]
        basic_field_validation_error = validate_fields(row, fields)
        if basic_field_validation_error is not None:
            return basic_field_validation_error
        # Assets can be None, when a portfolio starts
        snapshot_assets = row.get("assets", None)
        if len(snapshot_assets) > 0:
            assets_field_validation_error = validate_fields(snapshot_assets, subfields)
            if assets_field_validation_error is not None:
                raise Exception(
                    assets_field_validation_error
                    + " Missing fields in snapshot assets."
                )
    except Exception as e:
        print("Error occured while validating snapshot: ", e)
        raise


def validate_txns(data: dict, fields: list[str]) -> None:
    try:
        if "rows" not in data:
            raise Exception(generate_missing_field_error("rows"))
        if len(data["rows"]) > 0:
            for row in data["rows"]:
                basic_field_validation_error = validate_fields(row, fields)
                if basic_field_validation_error is not None:
                    raise Exception(basic_field_validation_error)
    except Exception as e:
        print("Error occured while validating txns: ", e)
        raise


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
        print("Error occured while fetching latest snapshot: ", e)
        raise


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
        return convert_txns_to_map_by_date(response.json()["rows"])
    except Exception as e:
        print("Error occured while fetching all transactions: ", e)
        return e


def generate_date_list(start_date, end_date):
    date_list = []
    current_date = start_date
    while current_date <= end_date:
        date_list.append(current_date)
        current_date = (
            datetime.strptime(current_date, "%Y-%m-%d") + timedelta(days=1)
        ).strftime("%Y-%m-%d")
    return date_list


def get_close_price_by_ticker(ticker: str) -> float:
    try:
        response = requests.request(
            method="get",
            url=GET_CLOSE_PRICE_BY_TICKER,
            headers={"Content-Type": "application/json"},
            json={"ticker": ticker},
            timeout=10,
        )
        response.raise_for_status()
        data = response.json()
        if "close_price" in data:
            return float(data["close_price"])
        else:
            raise ValueError("Close_price not found in response.")
    except Exception as e:
        print("Error occured while fetching ticker's close price: ", e)
        raise


def update_existing_stock_in_snapshot(snapshot_map, stock_txn):
    try:
        ticker = stock_txn.get("ticker")
        # positive for buy, negative for sell
        txn_value = stock_txn.get("price") * stock_txn.get("qty")
        txn_type = stock_txn.get("txn_type")

        # existing value, qty, cost_basis in the snapshot
        _, qty, cost_basis = snapshot_map["assets"]["stock"][ticker]

        if txn_type == "buy":
            # update cost basis, cost basis remains the same for sell
            cost_basis = ((cost_basis * qty) + (txn_value)) / (
                qty + stock_txn.get("qty")
            )

        # Update cash value
        snapshot_map["assets"]["cash"] -= txn_value
        qty += stock_txn.get("qty")

        if qty == 0:
            # remove the entry of all stocks are sold
            del snapshot_map["assets"]["stock"][ticker]
        else:
            # update the value if stock qty is non zero
            close_price = get_close_price_by_ticker(ticker)
            snapshot_map["assets"]["stock"][ticker] = [
                qty * close_price,
                qty,
                cost_basis,
            ]
    except Exception as e:
        print("Error occured while updating an existing transaction: ", e)
        raise


def update_new_stock_in_snapshot(snapshot_map, stock_txn):
    try:
        ticker = stock_txn.get("ticker")
        # positive for buy, negative for sell
        qty = stock_txn.get("qty")
        txn_value = qty * stock_txn.get("price")

        # update cash value
        snapshot_map["assets"]["cash"] -= txn_value

        close_price = get_close_price_by_ticker(ticker)
        snapshot_map["assets"]["stock"][ticker] = [
            close_price * qty,
            qty,
            stock_txn.get("price"),
        ]
    except Exception as e:
        print("Error occured while updating a new transaction: ", e)
        raise


def update_snapshot_with_stock_txn(snapshot_map, stock_txn):
    try:
        if stock_txn.get("ticker") in snapshot_map["assets"]["stock"]:
            update_existing_stock_in_snapshot(snapshot_map, stock_txn)
        else:
            update_new_stock_in_snapshot(snapshot_map, stock_txn)
    except Exception as e:
        print("Error occured while updating a stock transaction: ", e)
        raise


def update_snapshot_with_option_txn(snapshot_map, txn):
    try:
        snapshot_map["assets"]["option"].append(txn)
        option_premium = txn.get("qty") * txn.get("price") * 100
        # sell premium would be negative because sell qty is always negative
        snapshot_map["assets"]["cash"] -= option_premium

        # lower the cost basis of the stock if it exists
        ticker = txn.get("ticker")
        if ticker in snapshot_map["assets"]["stock"]:
            ticker_qty = snapshot_map["assets"]["stock"][ticker][1]
            snapshot_map["assets"]["stock"][ticker][2] -= (
                abs(option_premium) / ticker_qty
            )
    except Exception as e:
        print("Error occured while updating a stock transaction: ", e)
        raise


def process_txns_by_date(snapshot_map, current_date_txns):
    try:
        for txn in current_date_txns:
            entity_type = txn.get("entity_type")
            if entity_type == "cash":
                snapshot_map["assets"]["cash"] += txn.get("qty")
            if entity_type == "stock":
                update_snapshot_with_stock_txn(snapshot_map, txn)
            if entity_type in ["option-put", "option-call"]:
                update_snapshot_with_option_txn(snapshot_map, txn)
    except Exception as e:
        print("Error occured while updating a transaction: ", e)
        raise


def close_expired_options(current_date: str, options: list) -> list:
    try:
        current_active_options = []
        for option in options:
            option_expiry_date = option.get("expiry_date")
            if option_expiry_date > current_date:
                current_active_options.append(option)
        return current_active_options
    except Exception as e:
        print("Error occured while closing expired options: ", e)
        raise


def calculate_portfolio_value(snapshot_map: dict) -> float:
    try:
        total = snapshot_map["assets"]["cash"]
        for values in snapshot_map["assets"]["stock"].values():
            total += values[0]
        return total
    except Exception as e:
        print("Error occured while calculating portfolio total: ", e)
        raise


def get_updated_snapshots(snapshot_map, all_txns, date_list):
    try:
        updated_snapshots = []
        for current_date in date_list:
            snapshot_map["snapshot_date"] = current_date
            current_date_txns = all_txns.get(current_date, None)
            if current_date_txns is not None:
                process_txns_by_date(snapshot_map, current_date_txns)
            snapshot_map["assets"]["option"] = close_expired_options(
                current_date, snapshot_map["assets"]["option"]
            )
            snapshot_map["portfolio_value"] = calculate_portfolio_value(snapshot_map)
            updated_snapshots.append(copy.deepcopy(snapshot_map))
        return updated_snapshots
    except Exception as e:
        print("Error occured while updating snapshot: ", e)
        raise


def generate_daily_snapshot_by_portfolio(portfolio_id):
    try:
        snapshot_map = get_latest_snapshot_map(portfolio_id)
        if isinstance(snapshot_map, Exception):
            return False
        print("portfolio:", snapshot_map)
        from_date = (
            datetime.strptime(snapshot_map.get("snapshot_date", None), "%Y-%m-%d")
            + timedelta(days=1)
        ).strftime("%Y-%m-%d")
        # print(from_date)
        today_date = datetime.today().strftime("%Y-%m-%d")
        all_txns = get_all_transactions(portfolio_id, from_date, today_date)
        # print("\ntxns: ", all_txns)
        date_list = generate_date_list(from_date, today_date)
        # print("\ndate_list: ", date_list)
        updated_snapshots = get_updated_snapshots(snapshot_map, all_txns, date_list)
        print("\nfinal:\n")
        for s in updated_snapshots:
            print(s.get("snapshot_date"))
            print(s)
    except Exception as e:
        print("Error occured while generating daily snapshots: ", e)
        raise


"""
TODOS:
Add support for primuim collection when stock does not exist

query today's stock price, when calculating snapshot per day.
"""