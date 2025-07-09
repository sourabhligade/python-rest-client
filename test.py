import time
import requests
from delta_rest_client import DeltaRestClient, OrderType
from delta_rest_client.helpers import generate_signature_headers

# API credentials
api_key = 'EyAvYHSNHY09MfS12KDSQC6dcUZGlO'
api_secret = 'yqsYbHN3dtR7kunYfmTF0a4f9oSXzqJaFhej0Ke1blV4oseSDBy1Rk8jprCw'
base_url = 'https://testnet-api.delta.exchange'

# Initialize SDK client (for basic actions)
delta_client = DeltaRestClient(
    base_url=base_url,
    api_key=api_key,
    api_secret=api_secret,
    raise_for_status=False
)

try:
    print("🔍 Authenticating...")
    delta_client.get_assets()
    print("✅ Authenticated successfully!")

    # Choose product
    product_id = 84  # BTCUSDT-PERP
    product = delta_client.get_product(product_id)
    print(f"📊 Trading Product: {product['symbol']}")

    # Check balance
    wallet = delta_client.get_balances(product['settling_asset']['id'])
    print("💰 Wallet:", wallet)

    # Step 1: Place market buy order
    print("\n🚀 Placing Market Buy Order...")
    market_order = delta_client.place_order(
        product_id=product_id,
        size=1,
        side='buy',
        order_type=OrderType.MARKET
    )
    print("✅ Market Order Placed:", market_order)

    # Step 2: Compute SL & TP
    entry_price = market_order.get('price') or 100  # fallback
    print(f"🎯 Entry Price: {entry_price}")

    risk = 10
    sl_price = round(entry_price - risk, 2)
    tp_price = round(entry_price + 4 * risk, 2)

    print(f"📉 SL Price: {sl_price}")
    print(f"📈 TP Price: {tp_price}")

    # Signature headers generator
    def signed_headers(payload, method='POST'):
        timestamp = str(int(time.time() * 1000))
        return generate_signature_headers(
            api_key=api_key,
            api_secret=api_secret,
            request_path='/orders/trigger',
            method=method,
            timestamp=timestamp,
            body=payload
        )

    # Step 3: Place TP Trigger Order (Limit Sell)
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

    tp_response = requests.post(
        url=base_url + "/orders/trigger",
        headers=signed_headers(tp_payload),
        json=tp_payload
    )
    print("📈 TP Order Response:", tp_response.json())

    # Step 4: Place SL Trigger Order (Market Sell)
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

    sl_response = requests.post(
        url=base_url + "/orders/trigger",
        headers=signed_headers(sl_payload),
        json=sl_payload
    )
    print("📉 SL Order Response:", sl_response.json())

except Exception as e:
    print("❌ Exception:", str(e))
    if hasattr(e, 'response'):
        print("📄 Status:", getattr(e.response, 'status_code', 'Unknown'))
        print("📄 Response:", getattr(e.response, 'text', 'No text'))

    print("\n🔧 Troubleshooting:")
    print("1. Ensure testnet API key is valid")
    print("2. Confirm testnet account has funds")
    print("3. Verify product ID is correct")
