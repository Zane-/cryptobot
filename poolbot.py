from strategies import PoolProfitBot

def main():
    INTERVAL = 60 * 60 # 60 minutes
    FEEDERS = { # short term positions here, with initial investments and sell points
        'TRX': {
            'initial': 100,
            'sell_point': 115
        },
        'ADA': {
            'initial': 100,
            'sell_point': 130
        }
    }
    POOL = 'XLM' # long term position here
    PAIR = 'ETH' # pair to buy/sell things with
    bot = PoolProfitBot(INTERVAL, FEEDERS, POOL, PAIR)
    bot.start()

if __name__ == '__main__':
    main()
