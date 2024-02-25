GET_SNAPSHOT_BY_PORTFOLIO_DATE_URL = "http://127.0.0.1:12342/getSnapshotByPortfolio"

GET_TXNS_BY_PORTFOLIO_DATE_URL = "http://127.0.0.1:12342/getTransactionsByPortfolioDate"

GET_CLOSE_PRICE_BY_TICKER_URL = "http://127.0.0.1:12344/getClosePriceByTicker"

GET_MARKET_STATUS_BY_DATE_URL = "http://127.0.0.1:12344/getMarketStatusByDate"

ADD_SNAPSHOT_URL = "http://127.0.0.1:12342/addSnapshot"


def generate_missing_field_error(field_name):
    return f'Missing "{field_name}" in the input data.'


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
    "cash",
    "stock",
    "option",
]

TXNS_REQUIRED_FIELDS = [
    "date",
    "entity_type",
    "expiry_date",
    "price",
    "qty",
    "strike",
    "ticker",
    "txn_type",
]
