import time
import os
import requests
from dotenv import load_dotenv
from delta_rest_client import DeltaRestClient, OrderType
from delta_rest_client.helpers import generate_signature_headers

# Load API credentials from .env
load_dotenv()
api_key = os.getenv('api_key')
api_secret = os.getenv('api_secret')
base_url = os.getenv('base_url')


# Initialize Delta client
client = DeltaRestClient(
    base_url=base_url,
    api_key=api_key,
    api_secret=api_secret
)

# Choose product ID (e.g., BTCUSDT-PERP)
product_id = 84
product = client.get_product(product_id)
settling_asset_id = product["settling_asset"]["id"]

# Place market buy order
order = client.place_order(
    product_id=product_id,
    size=1,
    side="buy",
    order_type=OrderType.MARKET
)
entry_price = order.get("price", 100)

# Calculate SL/TP
risk = 10
sl_price = round(entry_price - risk, 2)
tp_price = round(entry_price + 4 * risk, 2)

# Signature generator
def sign_headers(payload):
    ts = str(int(time.time() * 1000))
    return generate_signature_headers(
        api_key=api_key,
        api_secret=api_secret,
        request_path="/orders/trigger",
        method="POST",
        timestamp=ts,
        body=payload
    )

# Place TP order (limit sell)
tp_payload = {
    "product_id": product_id,
    "size": 1,
    "side": "sell",
    "order_type": "limit_order",
    "limit_price": tp_price,
    "trigger_price": tp_price,
    "stop_order_type": "take_profit_order",
    "time_in_force": "gtc",
    "reduce_only": True
}
requests.post(
    url=base_url + "/orders/trigger",
    headers=sign_headers(tp_payload),
    json=tp_payload
)

# Place SL order (market sell)
sl_payload = {
    "product_id": product_id,
    "size": 1,
    "side": "sell",
    "order_type": "market_order",
    "trigger_price": sl_price,
    "stop_order_type": "stop_loss_order",
    "time_in_force": "gtc",
    "reduce_only": True
}
requests.post(
    url=base_url + "/orders/trigger",
    headers=sign_headers(sl_payload),
    json=sl_payload
)
