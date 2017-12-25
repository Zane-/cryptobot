import json
import gdax
from binance.client import Client

with open('api_keys.json') as f:
    keys = json.load(f)

gdax_client = gdax.AuthenticatedClient(keys['gdax']['api_key'], keys['gdax']['api_secret'], keys['gdax']['passphrase'])
binance_client = Client(keys['binance']['api_key'], keys['binance']['api_secret'])

public_gdax = gdax.PublicClient()

# Returns the amount of ltc convertable from eth on gdax
def get_eth_ltc_gdax(eth):
    btc = float(public_gdax.get_product_ticker(product_id='ETH-BTC')['price']) * eth;
    # reciprocal of LTC-BTC is BTC-LTC
    return 1/float(public_gdax.get_product_ticker(product_id='LTC-BTC')['price']) * btc

# Returns the amount of ltc convertable from eth on binance
def get_eth_ltc_binance(eth):
    return 1/float(binance_client.get_all_tickers()[-28]['price']) * eth

# Returns the ratio of eth-ltc on binance to eth-ltc on gdax
def get_exchange_ratio_eth_ltc():
    return get_eth_ltc_binance(1)/get_eth_ltc_gdax(1)

# withdrawal example from gdax
# withdrawal_data = {
#    "amount": 10.00,
#    "currency": "BTC",
#    "crypto_address": "0x5ad5769cd04681FeD900BCE3DDc877B50E83d469"
# }
# gdax_client.withdraw(withdrawal_data)

# process:
# send eth on gdax to binance, sell into ltc, send to gdax, repeat
