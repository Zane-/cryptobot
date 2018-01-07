import sys

from exchange_utils import *

def main(ticker, sell_percent, pair_percent, step_change, time_interval, pair):
    ticker_data = fetch_ticker(ticker, pair)
    price = ticker_data['last']
    pair_start = fetch_balance(pair)
    buy_order = limit_buy(ticker, pair_percent, price, pair)
    buy_quantity = buy_order['info']['origQty']
    buy_price = buy_order['info']['price']
    print(f'[+] BUY ORDER PLACED')
    # do not proceed until buy order is filled
    while len(exchange.fetch_open_orders(ticker + f'/{pair}')) > 0:
        print('[-] ORDER NOT FILLED')
    print(f'[+] BOUGHT {buy_quantity} {ticker} AT {buy_price}')
    sell_change = sell_percent + ticker_data['change']
    # keep decreasing percent change until everything is sold
    try:
        while fetch_balance(ticker, 'total') > 0:
            sell_price = price * (1 + sell_change/100)
            sell_order = limit_sell(ticker, 100, sell_price, pair)
            print(sell_order)
            current_percent = fetch_ticker(ticker)['change']
            print(f'[+] CURRENT PERCENTAGE: {current_percent}\n')
            print('[-] WAITING . . . PRESS CTRL+C TO SELL AT MARKET\n')
            sleep(time_interval)
            cancel_open_orders(ticker)
            sell_change -= step_change
    except (KeyboardInterrupt, EOFError):
        cancel_open_orders(ticker)
        sell_order = sell(ticker, 100)
        percent = fetch_ticker(ticker)['change']
        print(f'[-] SOLD THAT SHIT AT {percent}%\nDEVIANCE FROM GOAL: {sell_percent-percent}%')
        sys.exit()
    print('[+] SOLD EVERYTHING . . .')
    print(f'[+] TOTAL PROFIT/LOSS: {fetch_balance(pair) / pair_start * 100}')

if __name__ == '__main__':
    print('[+] CANCELLING ALL ORDERS . . . ')
    cancel_all_orders()
    sell_percent   = float(input('[+] ENTER PERCENTAGE INCREASE TO SELL:'))
    step_change    = float(input('[+] ENTER PERCENTAGE DECREASE STEP CHANGE:'))
    time_interval  = float(input('[+] ENTER TIME INTERVAL (SEC) TO EXECUTE STEPS:'))
    vol_percent    = float(input('[+] ENTER % OF ASSETS YOU WOULD LIKE TO RISK:'))
    pair           = input('[+] ENTER PAIR (BTC|ETH):').upper()
    input(f'[+] PRESS ENTER TO SELL {vol_percent}% OF ALL ASSETS INTO {pair}:')
    pair_before = fetch_balance(pair)
    pair_amount = pair_before * (vol_percent/100)
    sell_tickers(fetch_nonzero_balances(), vol_percent, pair=pair)
    pair_after = fetch_balance(pair)
    pair_percent = (pair_amount + pair_after - pair_before) / pair_after * 100
    ticker = input('[PUMP BOT 1.0] | ENTER TICKER TO START:').upper()
    while ticker + f'/{pair}' not in exchange.symbols: # validate ticker
        ticker = input(f'[-] TICKER {ticker} NOT FOUND, PLEASE RE-ENTER:\n').upper()
    main(ticker, sell_percent, 50, step_change, time_interval, pair)
