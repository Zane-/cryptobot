from time import sleep
import trade

def limit_sell(ticker, price):
    sell_placed = False
    while not sell_placed:
        try:
            order = trade.binance.create_limit_sell_order(
                ticker,
                floor(fetch_balance(ticker[0:-4]) * 0.985),
                price)
        except trade.ccxt.BaseError as e:
            print(e)
            continue
        sell_placed = True
    return order


def liquidate_watching():
    for ticker in trade.WATCHING:
            order = trade.sell(ticker, 100)
            print(order)


def main():
    eth = trade.fetch_balance('ETH')
    ticker = input('TICKER: ')
    ticker_data = trade.fetch_ticker(ticker)
    price = ticker_data['bid']
    trade.buy(ticker, price, eth)

    sell_percent = float(input('PERCENTAGE INCREASE TO SELL: '))
    sell_change = sell_percent + ticker_data['change']
    sell_price = price * (1 + sell_change/100)

    order = limit_sell(ticker, sell_price)
    print(order)

    ###               GRADIENT PERCENTAGE DECREASE               ###
    change_step = float(input('DECREASE STEP: '))
    timeout = float(input('TIMEOUT (SEC): '))
    sell_change -= change_step

    # while it hasn't sold
    while trade.fetch_balance(ticker[0:-4] >= 1):
        time.sleep(timeout)
        sell_price = price * (1 + sell_change/100)
        sell_canceled = False
        while not sell_canceled:
            try:
                trade.binance.cancel_order(order['orderId'], ticker)
            except trade.ccxt.BaseError as e:
                print(e)
                continue
            sell_canceled = True

        order = limit_sell(ticker, sell_price)
        print(order)
        sell_change -= change_step
    ###                                                          ###


if __name__ == '__main__':
    input("<[PUMP BOT 1.0 | PRESS ENTER TO START]>")
    #liquidate_watching()
    main() # start bot
