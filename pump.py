from exchange_utils import *


def main(symbol, pair_percentage, sell_percent):
    symbol_data = get_symbol(symbol)
    start_change = symbol_data['change']
    ticker, pair = symbol.split('/')
    ticker_start = get_balance(ticker)
    pair_start = get_balance(pair)
    # buy at market for now
    buy_order = buy(symbol, pair_percentage, auto_adjust=True)
    buy_quantity = buy_order['info']['origQty']
    buy_price = symbol_data['ask'] # use ask price because market order returns 0 as price
    print(f'[+] BUY ORDER FILLED: BOUGHT {buy_quantity} {ticker} AT {buy_price}')
    sell_change = sell_percent + start_change
    sell_price = float(buy_price) * (1 + sell_change/100)
    sell_order = sell(symbol, 100, sell_price, auto_adjust=True)
    sell_quantity = sell_order['info']['origQty']
    print(f'[+] SELLING {sell_quantity} {ticker} at {sell_price}')
    print('[+] PRESS CTRL+C TO SELL AT MARKET')

    try:
        # should be able to sell everything since we are using BNB to eat the fees
        while get_balance(ticker, 'total') > ticker_start:
            current_change = get_symbol(symbol)['change']
            print(f'[+] START CHANGE: {start_change} | CURRENT CHANGE: {current_change} | TARGET: {sell_change}')
            sleep(1)  # update change every 1 second
    except (KeyboardInterrupt, EOFError):
        exchange.cancel_order(sell_order['id'], symbol)
        sell_order = sell(symbol, 100, auto_adjust=True)
        sell_quantity = sell_order['info']['origQty']
        print(f'\n[-] SOLD {sell_quantity} {ticker} AT MARKET')

    print('[+] SOLD EVERYTHING . . .')
    print(f'[+] TOTAL PROFIT/LOSS: {100 *(get_balance(pair) / pair_start) - 100:.2f}%')


if __name__ == '__main__':
    print('[+] CANCELLING ALL ORDERS . . .')
    cancel_all_orders()

    sell_percent   = float(input('[+] ENTER PERCENTAGE INCREASE TO SELL: '))
    pair           = input('[+] ENTER PAIR (BTC|ETH): ').upper()

    pair_usd = get_usd_balance(pair)
    pair_balance = get_balance(pair)
    print(f'[+] YOU HAVE {pair_balance:.4f} TO RISK (${pair_usd:.2f})')
    pair_percentage = float(input(f'[+] ENTER % OF {pair} YOU WOULD LIKE TO RISK: '))
    print("[+] NOTE: PAIR % WILL AUTO ADJUST TO THE MINIMUM IF NOT MET (0.002 BTC|0.02 ETH)")

    pair_total = get_balance(pair) * pair_percentage/100
    pair_usd_total = pair_usd * pair_percentage/100
    print(f'[+] RISKING {pair_total:.6f} {pair} (${pair_usd_total:.2f})')

    ticker = input('[PUMP BOT READY] | ENTER TICKER TO START: ').upper()
    while f'{ticker}/{pair}' not in exchange.symbols:  # validate ticker
        ticker = input(f'[-] TICKER {ticker} NOT FOUND, PLEASE RE-ENTER: ').upper()
    symbol = f'{ticker}/{pair}'

    main(symbol, pair_percentage, sell_percent)
