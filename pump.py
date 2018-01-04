from time import sleep
from trade import *

def main():
    ticker = input('TICKER: ')
    ticker_data = trade.get_ticker_data(ticker)
    price = ticker_data['price']
    trade.buy(ticker, price, eth)

    sell_percent = float(input('PERCENTAGE INCREASE TO SELL: '))
    sell_change = sell_percent + ticker_data['change']
    sell_price = price * (1 + sell_change/100)
    sell_placed = False

    while not sell_placed:
        try:
            trade.b.order_limit_sell(
                symbol=ticker,
                quantity=floor(get_ticker_balance(ticker[0:-3])),
                price=sell_price)
        except (BinanceAPIException, BinanceOrderException) as e:
            print(e)
            continue
        sell_placed = True


    ###               GRADIENT PERCENTAGE DECREASE               ###
    change_step = float(input('DECREASE STEP: '))
    timeout = float(input('TIMEOUT (SEC): '))
    sell_change -= change_step

    # while it hasn't sold
    while get_ticker_balance(ticker[0:-3] >= 1):
        time.sleep(timeout)
        sell_price = price * (1 + sell_change/100)
        trade.b.cancel_order(
            symbol=ticker,
            orderId=trade.b.get_open_orders(symbol=ticker)[0]['orderId'])
        trade.b.order_limit_sell(
                symbol=ticker,
                quantity=floor(get_ticker_balance(ticker[0:-3])),
                price=sell_price)
        sell_change -= change_step
    ###                                                          ###

def liquidate_watching():
    for ticker in trade.WATCHING:
            try:
                trade.sell(ticker, 100)
            except (BinanceAPIException, BinanceOrderException) as e:
                print(e)

if __name__ == '__main__':
    input("<[PUMP BOT 1.0 | PRESS ENTER TO START]>")
    liquidate_watching()
    eth = trade.get_ticker_balance('ETH')
    main() # start bot
