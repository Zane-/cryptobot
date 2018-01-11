# Cryptocurrency Trading Bot. [![Build Status](https://travis-ci.com/Zane-/cryptobot.svg?token=ZPyhzVXub6P6TvJiSJZJ&branch=master)](https://travis-ci.com/Zane-/cryptobot)  

__Note: Any pushes to the master branch of this repo are immediately deployed to Heroku.__
## TODO:
* ~~Implement a scheduler within the script.~~
* ~~Add a testfile.~~
* Implement strategies using technical analysis  

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
