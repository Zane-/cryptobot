from strategies import BinanceNewListingBot

def main():
    INTERVAL = 3 # check every 3 seconds
    PAIR = 'ETH' # pair to buy/sell with
    PERCENTAGE = 100 # percentage of pair to buy with
    SELL_AFTER = True # whether or not to place a sell order directly after
    SELL_MULTIPLIER = 2
    bot = BinanceNewListingBot(INTERVAL, PAIR, PERCENTAGE, SELL_AFTER, SELL_MULTIPLIER)
    bot.start()

if __name__ == '__main__':
    main()
