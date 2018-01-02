import json
#import gdax
from binance.client import Client

#####~~~~~~~~~~~~~~~Key, Address, and Client Setup~~~~~~~~~~~~~~~~#####
with open('api_keys.json') as f:
    keys = json.load(f)

#with open('addresses.json') as f:
#    addresses = json.load(f)

#g = gdax.AuthenticatedClient(keys['gdax']['api_key'], keys['gdax']['api_secret'], keys['gdax']['passphrase'])
b = Client(keys['binance']['api_key'], keys['binance']['api_secret'])

#pg = gdax.PublicClient()
#####~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~#####