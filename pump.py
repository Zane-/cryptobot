import sys

from exchange_utils import *

def main(ticker, change_before, sell_percent, pair_percent, step_change, time_interval, pair):
    ticker_data = get_ticker(ticker, pair)
    price = ticker_data['bid'] # use last bid to determine buy price
    pair_start = get_balance(pair)

    buy_order = buy(ticker, pair, pair_percent, price, auto_adjust=True)
    print(f'[+] BUY ORDER PLACED {buy_order["amount"]} {ticker} AT {buy_order["price"]}')
    # do not proceed until buy order is filled
    while exchange.fetch_order(buy_order['id'], ticker + f'/{pair}')['status'] != 'closed':
        print('[-] ORDER NOT FILLED')
    print('[+] ORDER FILLED')
    # percentage is calculated from change when the ticker was entered
    # if you are slow on the enter, it could already be pumped up from what it was
    sell_change = sell_percent + change_before
    # keep decreasing percent change until everything is sold
    try:
        while get_balance(ticker, 'total') > 0:
            sell_price = price * (1 + sell_change/100)
            sell_order = sell(ticker, pair, 100, sell_price, auto_adjust=True)
            print(f'[+] SELLING {sell_order["amount"} {ticker} at {sell_order["price"]}')
            current_percent = get_ticker(ticker)['change']
            print(f'[+] CURRENT PERCENTAGE: {current_percent} PERCENT TIL TARGET: {sell_change - current_percent}')
            print('[-] WAITING . . . PRESS CTRL+C TO SELL AT MARKET')
            sleep(time_interval)
            cancel_order(sell_order)
            print('[-] ORDER CANCELED')
            sell_change -= step_change
    except (KeyboardInterrupt, EOFError):
        cancel_open_orders(ticker)
        percent = get_ticker(ticker)['change']
        sell_order = sell(ticker, pair, 100, auto_adjust=True)
        print(f'[-] SOLD THAT SHIT AT {percent}%\nDEVIANCE FROM GOAL: {sell_percent-percent}%')
        sys.exit()

    print('[+] SOLD EVERYTHING . . .')
    print(f'[+] TOTAL PROFIT/LOSS: {get_balance(pair) / pair_start * 100 - 100}')

if __name__ == '__main__':
    print('[+] PRELOADING TICKER DATA . . .')
    ticker_data = exchange.fetch_tickers()
    print('[+] CANCELLING ALL ORDERS . . .')
    cancel_all_orders()
    sell_percent   = float(input('[+] ENTER PERCENTAGE INCREASE TO SELL: '))
    step_change    = float(input('[+] ENTER PERCENTAGE DECREASE STEP CHANGE: '))
    time_interval  = float(input('[+] ENTER TIME INTERVAL (SEC) TO EXECUTE STEPS: '))
    pair           = input('[+] ENTER PAIR (BTC|ETH): ').upper()
    print(f'[+] YOU HAVE {get_balance(pair)} TO RISK (${get_usd_balance(pair)})')
    min_percent = ceil(MINIMUM_AMOUNTS[pair] * 100 / get_balance(pair))
    pair_percent   = float(input(f'[+] ENTER % OF {pair} YOU WOULD LIKE TO RISK: '))
    while pair_percent < min_percent:
        print(f'[-] DOES NOT SATISFY MINIMUM ORDER REQUIREMENTS: MINIMUM IS {min_percent}%')
        pair_percent = float(input(f'[+] RE-ENTER % OF {pair} YOU WOULD LIKE TO RISK: '))
    sell_alts = input(f'[+] WOULD YOU LIKE TO SELL ALTCOINS INTO {pair}? (y|*): ').upper()

    if sell_alts == 'Y':
        alt_percent = float(input(f'[+] ENTER % OF ALTS TO SELL INTO {pair}: '))
        pair_before = get_balance(pair)
        pair_amount = pair_before * (pair_percent/100)
        sell_tickers(get_nonzero_balances(), pair, alt_percent, auto_adjust=True)
        pair_after = get_balance(pair)
        print(f'[+] SOLD ALTCOINS FOR A GAIN OF {pair_after-pair_before} {pair}')
        pair_percent = (pair_amount + pair_after - pair_before) / pair_after * 100

    pair_total = get_balance(pair) * (pair_percent / 100)
    pair_usd_total = get_ticker(pair, 'USDT')['last'] * pair_total
    print(f'[+] RISKING {pair_total} {pair} (${pair_usd_total})')
    ticker = input('[PUMP BOT READY] | ENTER TICKER TO START: ').upper()
    while f'{ticker}/{pair}' not in exchange.symbols: # validate ticker
        ticker = input(f'[-] TICKER {ticker} NOT FOUND, PLEASE RE-ENTER: ').upper()
    change_before = ticker_data[f'{ticker}/{pair}']['change']
    main(ticker, change_before, sell_percent, pair_percent, step_change, time_interval, pair)
