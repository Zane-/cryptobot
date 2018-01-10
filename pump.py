import sys

from exchange_utils import *

def main(ticker, pair, pair_percentage, change_before, sell_percent, step_change, time_interval):
    ticker_data = get_ticker(ticker, pair)
    price = ticker_data['bid'] * 1.02 # use bid + 2% to try to buy in faster
    pair_start = get_balance(pair)
    ticker_start = get_balance(ticker)

    buy_order = buy(ticker, pair, pair_percentage, price, auto_adjust=True)

    try: # do not proceed until buy order is filled
        while not get_balance(ticker) > ticker_start:
            sleep(0.5) # avoid spamming api with checks
            print('[-] ORDER NOT FILLED . . . PRESS CTRL+C TO CANCEL AND EXIT')
    except (EOFError, KeyboardInterrupt): # ctrl+c to cancel order and exit
        cancel_orders(ticker)
        print('[-] ORDER CANCELED')
        sys.exit()

    print('[+] ORDER FILLED')
    # percentage is calculated from change when the ticker was entered
    # if you are slow on the enter, it could already be pumped up from what it was
    sell_change = sell_percent + change_before
    # keep decreasing percent change until everything is sold
    try:
        while get_balance(ticker, 'total') > 0:
            sell_price = price * (1 + sell_change/100)
            sell_order = sell(ticker, pair, 100, sell_price, auto_adjust=True)
            print(f'[+] SELLING {sell_order["info"]["origQty"]} {ticker} at {sell_order["info"]["price"]}')
            current_percent = get_ticker(ticker)['change']
            print(f'[+] CURRENT PERCENTAGE: {current_percent} | TARGET: {sell_change}')
            print('[-] WAITING . . . PRESS CTRL+C TO SELL AT MARKET')
            sleep(time_interval)
            cancel(sell_order)
            sell_change -= step_change
    except (KeyboardInterrupt, EOFError):
        cancel_orders(ticker)
        sell_order = sell(ticker, pair, 100, auto_adjust=True)
        print('[-] SOLD AT MARKET')
        sys.exit()

    print('[+] SOLD EVERYTHING . . .')
    print(f'[+] TOTAL PROFIT/LOSS: {get_balance(pair) / pair_start * 100 - 100}')

if __name__ == '__main__':
    print('[+] PRELOADING TICKER DATA . . .')
    ticker_data = get_all_tickers()
    print('[+] CANCELLING ALL ORDERS . . .')
    cancel_all_orders()
    sell_percent   = float(input('[+] ENTER PERCENTAGE INCREASE TO SELL: '))
    step_change    = float(input('[+] ENTER PERCENTAGE DECREASE STEP CHANGE: '))
    time_interval  = float(input('[+] ENTER TIME INTERVAL (SEC) TO EXECUTE STEPS: '))
    pair           = input('[+] ENTER PAIR (BTC|ETH): ').upper()
    pair_usd = get_usd_balance(pair)
    print(f'[+] YOU HAVE {get_balance(pair)} TO RISK (${pair_usd:.2f})')
    min_percent = ceil(exchange_config['MINIMUM_AMOUNTS'][pair] * 100 / get_balance(pair))
    pair_percentage = float(input(f'[+] ENTER % OF {pair} YOU WOULD LIKE TO RISK: '))
    while pair_percentage < min_percent:
        print(f'[-] DOES NOT SATISFY MINIMUM ORDER REQUIREMENTS: MINIMUM IS {min_percent}%')
        pair_percentage = float(input(f'[+] RE-ENTER % OF {pair} YOU WOULD LIKE TO RISK: '))

    pair_total = get_balance(pair) * pair_percentage/100
    pair_usd_total = pair_usd * pair_percentage/100
    print(f'[+] RISKING {pair_total} {pair} (${pair_usd_total:.2f})')
    ticker = input('[PUMP BOT READY] | ENTER TICKER TO START: ').upper()

    while f'{ticker}/{pair}' not in exchange.symbols: # validate ticker
        ticker = input(f'[-] TICKER {ticker} NOT FOUND, PLEASE RE-ENTER: ').upper()
    change_before = ticker_data[f'{ticker}/{pair}']['change']

    main(ticker, pair, pair_percentage, change_before, sell_percent, step_change, time_interval)
