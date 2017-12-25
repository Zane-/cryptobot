import json
import gdax
from binance.client import Client
from binance.exceptions import BinanceApiException, BinanceWithdrawException

#####~~~~~~~~~~~~~~~Key, Address, and Client Setup~~~~~~~~~~~~~~~~#####
with open('api_keys.json') as f:
    keys = json.load(f)

with open('addresses.json') as f:
    addresses = json.load(f)

gdax_client = gdax.AuthenticatedClient(keys['gdax']['api_key'], keys['gdax']['api_secret'], keys['gdax']['passphrase'])
binance_client = Client(keys['binance']['api_key'], keys['binance']['api_secret'])

public_gdax = gdax.PublicClient()
#####~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~#####

# Returns the last price of ETH-BTC on GDAX.
def get_eth_btc_gdax():
    return float(public_gdax.get_product_ticker(product_id='ETH-BTC')['price'])


# Returns the last price of LTC-BTC on GDAX.
def get_ltc_btc_gdax():
    return float(public_gdax.get_product_ticker(product_id='LTC-BTC')['price'])


# Returns the last price of ETH-LTC on binance.
def get_eth_ltc_binance():
    return 1/float(binance_client.get_ticker(symbol='LTCETH')['lastPrice'])


# Returns the amount of ETH convertable from LTC on GDAX.
# Fees are not taken into account because we will only be placing
# limit orders.
def convert_ltc_eth_gdax(ltc):
    btc = get_eth_btc_gdax() * eth;
    # reciprocal of LTC-BTC is BTC-LTC
    return 1/get_ltc_btc_gdax() * btc


# Returns the ratio of ETH-LTC on binance to ETH-LTC on GDAX.
def get_exchange_ratio_eth_ltc():
    return get_eth_ltc_binance(1) / get_eth_ltc_gdax(1)


# Places a limit sell order for LTC-BTC for the market price + a margin percentage,
# then places a buy order for ETH-BTC for the market price - a margin percentage on
# GDAX.
def sell_ltc_eth_dax(ltc, margin):
    gdax_client.sell(
            str(price=get_ltc_btc_gdax() * (1+margin)),
            size=str(ltc),
            product_id='LTC-BTC')
    gdax_client.buy(
            str(price=1/get_eth_btc_gdax * (1-margin)),
            # flush entire btc into eth (no btc in account before ltc is converted)
            size=gdax_client.get_account('441d62bd-681a-484c-9b1d-479946b943f6')['available'],
            product_id='ETH-BTC')


# Places a limit buy order for LTC using ETH on binance.
def buy_ltc_eth_binance(eth, margin):
    eth_ltc = get_eth_ltc_binance()
    price = 1/eth_btc * (1-margin)
    binance_client.order_limit_buy(
            symbol='LTCETH',
            # account for 0.050% fee
            amount=eth * eth_ltc * (99.95),
            price=price,
            disable_validation=True)
            

# Withdraws the specified amount of ether to the ETH address for binance.
# WARNING: No confirmation is given, and 2FA is bypassed, so double check
#          addresses given in addresses.json.
def withdraw_eth_gdax(eth):
    params = {
        'amount': eth,
        'currency': 'ETH',
        'crypto_address': addresses['eth-binance'] 
    }
    gdax_client.withdraw(params)


# Withdraws the specified amount of litecoin to the LTC address for GDAX.
# WARNING: No confirmation or validation occurs, so double check addresses
#          given in addresses.json.
def withdraw_ltc_binance(ltc):
    try:
        binance_client.withdraw(
                asset='LTC',
                address=addresses['ltc-gdax'],
                amount=ltc)
    except (BinanceApiException, BinanceWithdrawException) as e:
        with open('exceptions.log', 'w') as f:
            f.write(e)


# Cancels all open orders on GDAX and binance.
def cancel_all_orders():
    gdax_client.cancel_all(product='LTC-BTC')
    gdax_client.cancel_all(product='ETH-BTC')
    # TODO:
    # cancel binance orders, need to place order to see
    # format of binance_client.get_all_orders(symbol='LTCETH')

# process:
# if exchange rate of eth/ltc is greater than 1.02 (for fees),
# send eth on gdax to binance, sell into ltc, send to gdax, repeat

# TODO:
# * Add checks to see if withdrawals/deposits have cleared
# * Write the run function
# * Find hosting
