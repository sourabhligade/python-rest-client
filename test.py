import os
import time
import math
import requests
from dotenv import load_dotenv
from delta_rest_client import DeltaRestClient
from delta_rest_client.helpers import generate_signature_headers

# Load credentials
load_dotenv()
api_key = os.getenv("api_key")
api_secret = os.getenv("api_secret")
base_url = os.getenv("base_url")  # https://cdn-ind.testnet.deltaex.org

# Initialize REST client
delta_client = DeltaRestClient(
    base_url=base_url,
    api_key=api_key,
    api_secret=api_secret
)

# Product config (change this for different contracts)
product_id = 84  # Example: BTCUSDT perpetual
lot_size = 1

# Get current market price
product = delta_client.get_product(product_id)
tick_size = float(product['tick_size'])

# Get LTP (last traded price)
ltp = float(delta_client.get_ticker(product_id)['spot_price'])

# Entry price = current LTP
entry_price = round(ltp, 2)

# SL and TP as % of entry price
sl_percent = 0.02   # 2% loss
tp_percent = 0.10   # 10% gain

sl_trigger_price = round(entry_price * (1 - sl_percent), 2)
sl_limit_price = sl_trigger_price  # Can add buffer if needed

tp_trigger_price = round(entry_price * (1 + tp_percent), 2)
tp_limit_price = tp_trigger_price  # Can set slightly worse to ensure fill

# Round all prices to tick size
def round_to_tick(price, tick):
    return round(math.floor(price / tick) * tick, 2)

entry_price = round_to_tick(entry_price, tick_size)
sl_trigger_price = round_to_tick(sl_trigger_price, tick_size)
sl_limit_price = round_to_tick(sl_limit_price, tick_size)
tp_trigger_price = round_to_tick(tp_trigger_price, tick_size)
tp_limit_price = round_to_tick(tp_limit_price, tick_size)

# Final order payload
order_payload = {
    "product_id": product_id,
    "limit_price": entry_price,
    "size": lot_size,
    "side": "buy",
    "order_type": "limit_order",
    "stop_trigger_method": "last_traded_price",
    "bracket_stop_loss_limit_price": sl_limit_price,
    "bracket_stop_loss_price": sl_trigger_price,
    "bracket_take_profit_limit_price": tp_limit_price,
    "bracket_take_profit_price": tp_trigger_price,
    "time_in_force": "gtc"
}

# Generate signed headers manually (optional if SDK handles this)
timestamp = str(int(time.time() * 1000))
headers = generate_signature_headers(
    api_key=api_key,
    api_secret=api_secret,
    request_path="/v2/orders",
    method="POST",
    timestamp=timestamp,
    body=order_payload
)

# Send request using SDK (preferred)
response = delta_client.request("POST", "/v2/orders", order_payload, auth=True)

# Alternatively, send raw request:
# response = requests.post(base_url + "/v2/orders", headers=headers, json=order_payload)

print("Order response:")
print(response)
