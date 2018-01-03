## Cryptotrading Bot.

__Note: Any pushes to this repo are immediately deployed to Heroku__
### TODO:  
* Add dropbox support for download/updating/uploading the transactions.csv file. Heroku does not support writing to the local directory.
* Implement a scheduler within the script (add an infinite loop in the main method). Heroku's scheduler can only be run daily or hourly. Ideally we would like to fine tune the trade interval more.
* 

### Installing Requirements:
`pip install -r requirements.txt`


### Getting API Keys:
Generate key for binance: https://www.binance.com/userCenter/createApi.html
Enable IP Address Restriction and Withdrawals, write down secret key.  

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
