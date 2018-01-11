# Cryptotrading Bot.

__Note: Any pushes to the master branch of this repo are immediately deployed to Heroku__
## TODO:
* ~~Implement a scheduler within the script (add an infinite loop in the main method). Heroku's scheduler can only be run daily or hourly. Ideally we would like to fine tune the trade interval more.~~
* ~~Add a testfile (you can place test orders with the binance api).~~
* Implement strategies using technical analysis  

## Installing Requirements:
`pip install -r requirements.txt`  
## Getting API Keys:
* Generate keys for binance: https://www.binance.com/userCenter/createApi.html  
* Add the keys to a file named `api_keys.json`  
## Format of api_keys.json:
~~~
{
    "exchange_name": {
        "api_key": "public api key here",
        "api_secret": "secret key here"
    }
}
~~~
