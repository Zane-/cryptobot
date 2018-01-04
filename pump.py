from time import sleep
from trade import *

def main():
    ticker = input('TICKER: ')
    ticker_data = trade.fetch_ticker(ticker)
    price = ticker_data['bid']
    trade.buy(ticker, price, eth)

    sell_percent = float(input('PERCENTAGE INCREASE TO SELL: '))
    sell_change = sell_percent + ticker_data['change']
    sell_price = price * (1 + sell_change/100)
    sell_placed = False

    while not sell_placed:
        try:
            order = trade.binance.create_limit_sell_order(
                ticker,
                floor(fetch_balance(ticker[0:-4])),
                sell_price)
        except trade.ccxt.BaseError as e:
            print(e)
            continue
        sell_placed = True


    ###               GRADIENT PERCENTAGE DECREASE               ###
    change_step = float(input('DECREASE STEP: '))
    timeout = float(input('TIMEOUT (SEC): '))
    sell_change -= change_step

    # while it hasn't sold
    while fetch_balance(ticker[0:-4] >= 1):
        time.sleep(timeout)
        sell_price = price * (1 + sell_change/100)
        trade.binance.cancel_order(order['orderId'], ticker)
        order = trade.binance.create_limit_sell_order(
                ticker,
                floor(get_ticker_balance(ticker[0:-3])),
                sell_price)
        sell_change -= change_step
    ###                                                          ###

def liquidate_watching():
    for ticker in trade.WATCHING:
            trade.sell(ticker, 1.0)

if __name__ == '__main__':
    input("<[PUMP BOT 1.0 | PRESS ENTER TO START]>")
    liquidate_watching()
    eth = trade.fetch_balance('ETH')
    main() # start bot
