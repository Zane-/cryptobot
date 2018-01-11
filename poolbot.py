from strategies import PoolProfitBot

def main():
    INTERVAL = 60 * 60 # 60 minutes
    FEEDERS = ['TRX', 'XVG'] # list shitcoins you're invested in here
    POOL = 'XLM' # long term position here
    PAIR = 'BTC' # pair to buy/sell things with
    BASE_AMOUNT = 10 # base investment in USD
    PROFIT_THRESHOLD = 2 # amount in USD to beconsidered profit, profit gets sold into pool
    bot = PoolProfitBot(INTERVAL, POOL, FEEDERS, PAIR, BASE_AMOUNT, PROFIT_THRESHOLD)
    bot.start()

if __name__ == '__main__':
    main()
