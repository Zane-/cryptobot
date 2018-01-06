from exchange_utils import *

def main(ticker, sell_percent, vol_percentage, step_change, time_interval):
    ticker_data = fetch_ticker(ticker)
    eth = fetch_balance('ETH')
    price = ticker_data['bid']
    amount = eth / price
    # buy(ticker, price, eth)

    sell_change = sell_percent + ticker_data['change']

    # keep decreasing percent change until everything is sold
    while fetch_balance(ticker[:-4], 'total') > 0:
        sell_price = price * (1 + sell_change/100)
        order = limit_sell(ticker, vol_percentage, sell_price)
        print(order)
        sleep(time_interval)
        cancel_open_orders(ticker)
        sell_change -= step_change


if __name__ == '__main__':
    sell_percent = float(input("ENTER PERCENTAGE INCREASE TO SELL\n"))
    vol_percent = float(input("ENTER % OF ASSETS YOU WOULD LIKE TO RISK\n"))
    step_change = float(input("ENTER PERCENTAGE DECREASE STEP CHANGE\n"))
    time_interval  = float(input("ENTER TIME INTERVAL (SEC) TO EXECUTE STEPS\n"))
    pair = input('ENTER ETH OR BTC AS PAIR\n')
    input("PRESS ENTER TO SELL COINS INTO ETHEREUM\n")
    cancel_all_orders()
    # sell_tickers(fetch_nonzero_balances(), pair=pair)
    ticker = input("[PUMP BOT 1.0] | ENTER THE TICKER TO START\n")
    main(ticker + f'/{pair.upper()}', sell_percent, vol_percent, step_change, time_interval) # start bot
