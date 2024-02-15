from flask import jsonify


GET_TXN_BY_PORTFOLIO_DATE_URL = "http://127.0.0.1:12342/getSnapshotByPortfolio"


def generate_missing_field_error(field_name):
    return f'Missing "{field_name}" in the input data'


def validate_fields(data, required_field):
    for field_name in required_field:
        if field_name not in data:
            return generate_missing_field_error(field_name)
    return None


SNAPSHOT_REQUIRED_FIELDS = [
    "portfolio_value",
    "snapshot_date",
    "assets",
    "snapshot_date",
]
SNAPSHOT_ASSETS_REQUIRED_FIELDS = [
    "entity_type",
    "ticker",
    "value",
    "qty",
    "cost_basis",
    "expiry_date",
]
