from math import floor
from time import sleep

from exchange_utils import *

WATCHING = ['ICX', 'TRX', 'XLM', 'ADA', 'IOTA', 'XRP', 'NAV', 'XVG']

def main(ticker, sell_percent, change_step, time_interval):
    eth = fetch_balance('ETH')

    ticker_data = fetch_ticker(ticker)
    price = ticker_data['bid']
    buy(ticker, price, eth)

    sell_change = sell_percent + ticker_data['change']
    sell_price = price * (1 + sell_change/100)

    order = limit_sell(ticker, sell_price)
    print(order)

    ###               GRADIENT PERCENTAGE DECREASE               ###
    # while it hasn't sold
    while fetch_balance(ticker[0:-4]) >= 1:
        time.sleep(time_interval)
        sell_change -= step_change
        sell_price = price * (1 + sell_change/100)
        sell_canceled = False
        while not sell_canceled:
            try:
                exchange.cancel_order(order['orderId'], ticker)
            except ccxt.BaseError as e:
                print(e)
                continue
            sell_canceled = True

        order = limit_sell(ticker, sell_price)
        print(order)
    ###                                                          ###


if __name__ == '__main__':
    sell_percent = float(input("<[PUMP BOT 1.0 | ENTER PERCENTAGE INCREASE TO SELL]>\n"))
    step_change = float(input("<[PUMP BOT 1.0 | ENTER PERCENTAGE STEP CHANGE]>\n"))
    time_interval  = float(input("<[PUMP BOT 1.0 | ENTER TIME INTERVAL (SEC) TO EXECUTE STEPS]>\n"))
    input("<[PUMP BOT 1.0 | PRESS ENTER TO SELL COINS INTO ETHEREUM]>\n")
    cancel_all_orders(fetch_nonzero_balances(WATCHING))
    liquidate_watching()
    ticker = input("<[PUMP BOT 1.0 | ENTER THE TICKER AND PRESS ENTER TO START]>\n")


    main(ticker, sell_percent, change_step, time_interval) # start bot
