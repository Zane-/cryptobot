from exchange_utils import *

def main(ticker, sell_percent, pair_percent, step_change, time_interval, pair):
    buy(ticker, pair_percent, pair)
    ticker_data = fetch_ticker(ticker, pair)
    price = ticker_data['bid']
    sell_change = sell_percent + ticker_data['change']
    # keep decreasing percent change until everything is sold
    while fetch_balance(ticker, 'total') > 0:
        sell_price = price * (1 + sell_change/100)
        order = limit_sell(ticker, 100, sell_price, pair)
        print(order)
        sleep(time_interval)
        cancel_open_orders(ticker)
        sell_change -= step_change

if __name__ == '__main__':
    sell_percent   = float(input('ENTER PERCENTAGE INCREASE TO SELL:\n'))
    step_change    = float(input('ENTER PERCENTAGE DECREASE STEP CHANGE:\n'))
    time_interval  = float(input('ENTER TIME INTERVAL (SEC) TO EXECUTE STEPS:\n'))
    vol_percent    = float(input('ENTER % OF ASSETS YOU WOULD LIKE TO RISK:\n'))
    pair           = input('ENTER PAIR (BTC | ETH):\n').upper()
    input(f'PRESS ENTER TO SELL {vol_percent}% OF ALL ASSETS INTO {pair}:\n')
    cancel_all_orders()
    pair_before = fetch_balance(pair)
    pair_amount = pair_before * (vol_percent/100)
    sell_tickers(fetch_nonzero_balances(), vol_percent, pair=pair)
    pair_after = fetch_balance(pair)
    pair_percent = (pair_amount + pair_after - pair_before) / pair_after
    ticker = input('[PUMP BOT 1.0] | ENTER TICKER TO START:\n')
    main(ticker, sell_percent, pair_percent, step_change, time_interval, pair)
