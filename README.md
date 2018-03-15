# Cryptocurrency Trading Bot.

## Installing Requirements:
`pip install -r requirements.txt`  
## Getting API Keys:
* Generate keys for binance: https://www.binance.com/userCenter/createApi.html  
* Add the keys to a file named `api_keys.json` in the same directory
    ### Format of api_keys.json:
    ```
    {
        "exchange_name": {
            "api_key": "public api key here",
            "api_secret": "secret key here"
        }
    }
    ```
## Changing Exchanges
* In auth.py, change  ccxt.binance to ccxt.exchange_of_your_choice, see [ccxt](https://github.com/ccxt/ccxt) documentation for a list of supported exchanges. I've tried to make sure all the functions in exchange_utils work across any exchange, but they have only been thouroughly tested on Binance.  
Example:
```python
exchange = ccxt.bittrex({
    'apiKey': keys['bittrex']['api_key'],
    'secret': keys['bittrex']['api_secret'],
})
```
