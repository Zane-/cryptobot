import sys

from exchange_utils import *

def main(ticker, sell_percent, pair_percent, step_change, time_interval, pair):
    ticker_data = fetch_ticker(ticker, pair)
    price = ticker_data['bid']
    pair_start = fetch_balance(pair)
    buy_order = limit_buy(ticker, pair_percent, price, pair)
    buy_quantity = buy_order['info']['origQty']
    buy_price = buy_order['info']['price']
    print(f'[+] BUY ORDER PLACED')
    # do not proceed until buy order is filled
    while len(exchange.fetch_open_orders(ticker + f'/{pair}')) > 0:
        print('[-] ORDER NOT FILLED')
    print(f'[+] BOUGHT {buy_quantity} {ticker} AT {buy_price}')
    # percentage is calculated from change when the ticker was entered
    # if you are slow on the enter, it could already be pumped up from what it was
    sell_change = sell_percent + ticker_data['change']
    # keep decreasing percent change until everything is sold
    try:
        while fetch_balance(ticker, 'total') > 0:
            sell_price = price * (1 + sell_change/100)
            sell_order = limit_sell(ticker, 100, sell_price, pair)
            print(f'[+] SELLING {sell_order["info"]["origQty"]} {ticker} at {sell_order["info"]["price"]}')
            current_percent = fetch_ticker(ticker)['change']
            print(f'[+] CURRENT PERCENTAGE: {current_percent}')
            print('[-] WAITING . . . PRESS CTRL+C TO SELL AT MARKET')
            sleep(time_interval)
            cancel_open_orders(ticker)
            print('[-] ORDER CANCELED')
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
    sell_percent   = float(input('[+] ENTER PERCENTAGE INCREASE TO SELL: '))
    step_change    = float(input('[+] ENTER PERCENTAGE DECREASE STEP CHANGE: '))
    time_interval  = float(input('[+] ENTER TIME INTERVAL (SEC) TO EXECUTE STEPS: '))
    pair           = input('[+] ENTER PAIR (BTC|ETH): ').upper()
    print(f'[+] YOU HAVE {fetch_balance(pair)} TO RISK (${get_pair_usd_balance(pair)})')
    pair_percent   = float(input(f'[+] ENTER % OF {pair} YOU WOULD LIKE TO RISK: '))
    sell_alts      = input(f'[+] WOULD YOU LIKE TO SELL ALTCOINS INTO {pair}? (y|n): ').upper()

    if sell_alts == 'Y':
        alt_percent = float(input(f'[+] ENTER % OF ALTS TO SELL INTO {pair}: '))
        pair_before = fetch_balance(pair)
        pair_amount = pair_before * (pair_percent/100)
        sell_tickers(fetch_nonzero_balances(), vol_percent, pair=pair)
        pair_after = fetch_balance(pair)
        print(f'[+] SOLD ALTCOINS FOR A GAIN OF {pair_after-pair_before} {pair}')
        pair_percent = (pair_amount + pair_after - pair_before) / pair_after * 100
    pair_total = fetch_balance(pair) * (pair_percent / 100)
    pair_usd_total = fetch_ticker(pair, 'USDT')['last'] * pair_total
    print(f'[+] RISKING {pair_total} {pair} (${pair_usd_total})')
    ticker = input('[PUMP BOT READY] | ENTER TICKER TO START: ').upper()
    while ticker + f'/{pair}' not in exchange.symbols: # validate ticker
        ticker = input(f'[-] TICKER {ticker} NOT FOUND, PLEASE RE-ENTER: ').upper()

    main(ticker, sell_percent, pair_percent, step_change, time_interval, pair)
