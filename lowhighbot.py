from strategies import LowHighPairBot


def main():
    NUM = 2 # number of high/low pairs to swap
    RUN_HOURS = [0, 6, 12, 18] # UTC hours to run at
    WATCHING = ['ICX', 'TRX', 'XLM', 'ADA', 'POWR', 'XRP', 'NAV', 'XVG']
    PAIR = 'ETH'
    SELL_PERCENT = 50 # percent of ticker to sell off each time
    bot = LowHighPairBot(NUM, RUN_HOURS, WATCHING, PAIR, SELL_PERCENT)
    bot.start()

if __name__ == '__main__':
    main()
