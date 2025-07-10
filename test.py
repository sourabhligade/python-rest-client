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

# Check env variables
assert api_key and api_secret and base_url, "❌ Missing .env values"
print(f"API Key: {api_key}\nBase URL: {base_url}")

# Initialize Delta client
client = DeltaRestClient(
    base_url=base_url,
    api_key=api_key,
    api_secret=api_secret
)

# Choose product (BTCUSDT-PERP = ID 84)
product_id = 84
product = client.get_product(product_id)
settling_asset_id = product["settling_asset"]["id"]

# Step 1: Place Market Buy Order
order = client.place_order(
    product_id=product_id,
    size=1,
    side="buy",
    order_type=OrderType.MARKET
)

# Get entry price
entry_price = float(order.get("average_fill_price") or order.get("price") or 100)
print("✅ Market Buy Order:", order)
print(f"🎯 Entry Price: {entry_price}")

# Step 2: Calculate SL & TP prices
risk = 10
sl_price = round(entry_price - risk, 2)
tp_price = round(entry_price + 4 * risk, 2)
print(f"📉 SL Price: {sl_price}")
print(f"📈 TP Price: {tp_price}")

# Step 3: Sign headers for /v2/orders
def sign_headers(payload):
    timestamp = str(int(time.time() * 1000))
    return generate_signature_headers(
        api_key=api_key,
        api_secret=api_secret,
        request_path="/v2/orders",
        method="POST",
        timestamp=timestamp,
        body=payload
    )

# Step 4: Place Take-Profit Order
tp_payload = {
    "product_id": product_id,
    "size": 1,
    "side": "sell",
    "order_type": "limit_order",
    "limit_price": tp_price,
    "stop_price": tp_price,
    "stop_order_type": "take_profit_order",
    "time_in_force": "gtc",
    "reduce_only": True
}

tp_response = requests.post(
    url=base_url + "/v2/orders",
    headers=sign_headers(tp_payload),
    json=tp_payload
)
print("📈 TP Response:", tp_response.status_code)
try:
    print("TP JSON:", tp_response.json())
except Exception as e:
    print("❌ TP JSON decode error:", e)
    print("🔍 TP Raw Response:", tp_response.text)

# Step 5: Place Stop-Loss Order
sl_payload = {
    "product_id": product_id,
    "size": 1,
    "side": "sell",
    "order_type": "market_order",
    "stop_price": sl_price,
    "stop_order_type": "stop_loss_order",
    "time_in_force": "gtc",
    "reduce_only": True
}

sl_response = requests.post(
    url=base_url + "/v2/orders",
    headers=sign_headers(sl_payload),
    json=sl_payload
)
print("📉 SL Response:", sl_response.status_code)
try:
    print("SL JSON:", sl_response.json())
except Exception as e:
    print("❌ SL JSON decode error:", e)
    print("🔍 SL Raw Response:", sl_response.text)
