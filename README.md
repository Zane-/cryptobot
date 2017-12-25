## Cryptotrading Bot.
### Format of api_keys.json:
~~~
{
    "gdax": {
        "api_key": "public api key here",
        "api_secret": "secret key here",
        "passphrase": "passphrase here"
    },
    "binance": {
        "api_key": "public api key here",
        "api_secret": "secret key here"
    }
}
~~~  
Place file in same directory as trade.py.

### Installing Requirements:
`pip install python-binance`  
`pip install gdax`

### Getting API Keys:
Generate key for GDAX: https://www.gdax.com/settings/api  
Enable all permissions, Create API Key, write down secret key and passphrase.  
  
Generate key for binance: https://www.binance.com/userCenter/createApi.html  
Enable IP Address Restriction and Withdrawals, write down secret key.
