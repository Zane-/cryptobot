import json
import ccxt

#####~~~~~~~~~~~~~~~Key, Address, and Client Setup~~~~~~~~~~~~~~~~#####
with open('api_keys.json') as f:
    keys = json.load(f)

#with open('addresses.json') as f:
#    addresses = json.load(f)

exchange = ccxt.binance({
    'apiKey': keys['binance']['api_key'],
    'secret': keys['binance']['api_secret'],
})
#####~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~#####