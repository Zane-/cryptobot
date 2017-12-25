import json
import gdax
from binance.client import Client

with open('api_keys.json') as f:
    keys = json.load(f)

gdax_client = gdax.AuthenticatedClient(keys['gdax']['api_key'], keys['gdax']['api_secret'], keys['gdax']['passphrase'])
binance_client = Client(keys['binance']['api_key'], keys['binance']['api_secret'])

public_gdax = gdax.PublicClient()

def get_eth_btc_gdax():
    return float(public_gdax.get_product_ticker(product_id='ETH-BTC')['price'])

def get_ltc_btc_gdax():
    return float(public_gdax.get_product_ticker(product_id='LTC-BTC')['price'])

def get_eth_ltc_binance():
    return 1/float(binance_client.get_ticker(symbol='LTCETH')['lastPrice'])

# Returns the amount of eth convertable from ltc on gdax.
# Fees are not taken into account because we will only be placing
# limit orders.
def convert_ltc_eth_gdax(ltc):
    btc = get_eth_btc_gdax() * eth;
    # reciprocal of LTC-BTC is BTC-LTC
    return 1/get_ltc_btc_gdax() * btc

# Returns the amount of ltc convertable from eth on binance.
# A fee of 0.050% is subtracted from the total amount.
def convert_eth_ltc_binance(eth, fee=0.050):
    return eth * get_eth_ltc_binance() * (1-fee)

# Returns the ratio of eth-ltc on binance to eth-ltc on gdax
def get_exchange_ratio_eth_ltc():
    return get_eth_ltc_binance(1)/get_eth_ltc_gdax(1)

# Places a limit sell order for LTC-BTC for the market price + a margin percentage,
# then places a buy order for ETH-BTC for the market price - a margin percentage.
def convert_ltc_eth_gdax(ltc, margin):
    gdax_client.sell(
            str(price=get_ltc_btc_gdax()*(1+margin)),
            size=str(ltc),
            product_id='LTC-BTC'
    )
    gdax_client.buy(
            str(price=1/get_eth_btc_gdax*(1-margin)),
            # flush entire btc into eth (no btc in account before ltc is converted)
            size=gdax_client.get_account('441d62bd-681a-484c-9b1d-479946b943f6')['available'],
            product_id='ETH-BTC'
    )

# Withdraws the specified amount of ether to the specified address.
# WARNING: No confirmation is given, and 2FA is bypassed.
def withdraw_eth_gdax(eth, address):
    params = {
        'amount': eth.
        'currency': 'ETH',
        'crypto_address': address
    }
    gdax_client.withdraw(params)
    
# process:
# send eth on gdax to binance, sell into ltc, send to gdax, repeat
