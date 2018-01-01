## Cryptotrading Bot.
### Format of api_keys.json:
~~~
{
    "binance": {
        "api_key": "public api key here",
        "api_secret": "secret key here"
    }
}
~~~
Place file in same directory as trade.py.

### Installing Requirements:
`pip install python-binance`
`pip install apscheduler`

### Getting API Keys:
Generate key for binance: https://www.binance.com/userCenter/createApi.html
Enable IP Address Restriction and Withdrawals, write down secret key.
