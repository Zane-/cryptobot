import re
from math import ceil, floor
from time import sleep

from auth import *


# Decorator to retry functions upon ccxt NetworkErrors exceptions.
# Interval is the sime in seconds to wait, and retries is the number of retries.
def network_error_retry(interval=1, retries=5):
    def decorator(func):
        def wrapper(*args, **kwargs):
            for _ in range(retries):
                try:
                    return func(*args, **kwargs)
                except ccxt.NetworkError as e:
                    print(f'A network error occured. Retrying in {interval} seconds.')
                    sleep(interval)
            return None
        return wrapper
    return decorator


# Returns the balance of the ticker in the account.
# account='total' returns the total balance, even from open orders.
@network_error_retry(2)
def get_balance(ticker, account='free'):
    return float(exchange.fetch_balance()[ticker][account])


# Returns a list of tickers with non-zero balances in the account.
@network_error_retry(2)
def get_nonzero_balances(account='total'):
    balances = exchange.fetch_balance()[account]
    return {asset: balances[asset] for asset in balances.keys() if balances[asset] > 0}


# Returns data for the ticker.
@network_error_retry(2)
def get_symbol(symbol):
    data = exchange.fetch_ticker(symbol)
    return {
        'bid': data['bid'],
        'ask': data['ask'],
        'last': data['last'],
        'open': data['open'],
        'close': data['close'],
        'high': data['high'],
        'low': data['low'],
        'change': data['change'],
        'volume': data['quoteVolume']
    }


# Returns a dictionary w/ data on all symbols on the exchange.
def get_all_symbols():
    data = exchange.fetch_tickers()
    symbols = {}
    for symbol in data:
        symbols[symbol] = {
            'bid': data[symbol]['bid'],
            'ask': data[symbol]['ask'],
            'last': data[symbol]['last'],
            'open': data[symbol]['open'],
            'close': data[symbol]['close'],
            'high': data[symbol]['high'],
            'low': data[symbol]['low'],
            'change': data[symbol]['change'],
            'volume': data[symbol]['quoteVolume']
        }
    return symbols


# rounds down a float to the specified precision: round_down(12.3556, 3) -> 12.355
round_down = lambda n, p: round(floor(n/10**-p)*10**-p, p)

# Places a sell order for the ticker and pair using the given percentage of the ticker.
# Pass in a price for the price parameter to post a limit order.
# auto_adjust sets the amount as the minimum amount if the minimum amount is not reached.
@network_error_retry(2)
def sell(symbol, percentage, price='market', *, auto_adjust=False):
    ticker, pair = symbol.split('/')
    limits = exchange.markets[symbol]['limits']
    precision = exchange.markets[symbol]['precision']['amount']

    price = get_symbol(symbol)['ask'] if price == 'market' else float(exchange.price_to_precision(symbol, price))
    min_price = limits['price']['min']
    if price < min_price:
        if auto_adjust:
            price = min_price
        else:
            raise ccxt.InvalidOrder(f'Order price is below minimum of {min_price}')

    ticker_balance = get_balance(ticker)
    # round down amount to avoid api auto rounding the wrong way, causing an insufficient fund exception
    amount = round_down(ticker_balance * percentage/100, precision)
    pair_min = limits['cost']['min']
    min_amount = pair_min / price
    if amount < min_amount:
        if auto_adjust:
            amount = min_amount
        else:
            raise ccxt.InvalidOrder(f'Order does not meet minimum requirement of {pair_min} {pair}')

    if amount > ticker_balance:
        raise ccxt.InsufficientFunds('Insufficient funds to place this order')

    if price == 'market':
        return exchange.create_market_sell_order(symbol, amount)
    else:
        return exchange.create_limit_sell_order(symbol, amount, price)


# Places a buy order for the ticker and pair using the given percentage of the ticker.
# Pass in a price for the price parameter to post a limit order.
# auto_adjust sets the amount/price as the minimum amount if the minimum amount is not reached.
@network_error_retry(2)
def buy(symbol, percentage, price='market', *, auto_adjust=False):
    ticker, pair = symbol.split('/')
    limits = exchange.markets[symbol]['limits']
    precision = exchange.markets[symbol]['precision']['amount']

    price = get_symbol(symbol)['ask'] if price == 'market' else float(exchange.price_to_precision(symbol, price))
    min_price = limits['price']['min']
    if price < min_price:
        if auto_adjust:
            price = min_price
        else:
            raise ccxt.InvalidOrder(f'Order price is below minimum of {min_price}')

    pair_balance = get_balance(pair)
    pair_amount = pair_balance * percentage/100
    # round down amount to avoid api auto rounding the wrong way, causing an insufficient fund exception
    amount = round_down(pair_amount / price, precision)
    pair_min = limits['cost']['min']
    min_amount = pair_min / price
    if amount < min_amount:
        if auto_adjust:
            amount = min_amount
        else:
            raise ccxt.InvalidOrder(f'Order does not meet minimum requirement of {pair_min} {pair}')

    if amount * price > pair_balance:
        raise ccxt.InsufficientFunds(f'Insufficient funds to place this order.')

    if price == 'market':
        return exchange.create_market_buy_order(symbol, amount)
    else:
        return exchange.create_limit_buy_order(symbol, amount, price)


# Swaps a given percentage this into that at market. This and that must
# share a common pair.
def swap(this, that, percentage, *, auto_adjust=False):
    sell_order = sell(this, percentage, auto_adjust=auto_adjust)

    pair_amount = sell_order['info']['origQty'] * sell['info']['price']
    pair_percentage = pair_amount / get_balance(pair) * 100

    buy_order = buy(that, percentage, auto_adjust=auto_adjust)
    return (sell_order, buy_order)


# Returns all open orders for the ticker passed in. Returns a dictionary divided
# into lists for buy and sell orders.
@network_error_retry(2)
def get_open_orders(ticker):
    orders = {'buy': [], 'sell': []}
    symbols = [symbol for symbol in exchange.symbols if symbol.startswith(ticker)]
    for symbol in symbols:
        if symbol in exchange.symbols:
            for order in exchange.fetch_open_orders(symbol):
                orders[order['side']].append(order)
    return orders


# Cancels an order given the order dictionary returned by buy/sell.
@network_error_retry(2)
def cancel(order):
    symbol = order['info']['symbol']
    # parse order symbol because JSON response can be different than ccxt's
    # unified representation of symbols
    pairs = set(symbol.split('/')[1] for symbol in exchange.symbols)
    pairs_regex = '|'.join(pairs)
    symbol_regex = re.compile(f'(\\w+)({pairs_regex})')
    match = symbol_regex.match(symbol)
    if match:
        exchange.cancel_order(order['id'], match[1] + f'/{match[2]}')
        return True
    return False


# Cancels orders for the ticker on the specified side.
# side='both' cancels all orders, side='buy' cancels buy,
# side='sell cancels all sell orders.
def cancel_orders(ticker, side='both'):
    orders = get_open_orders(ticker)
    if side == 'both':
        cancels = []
        cancels.extend(orders['sell'])
        cancels.extend(orders['buy'])
    else:
        cancels = orders[side]
    for order in cancels:
        cancel(order)


# Cancels all open orders for the given tickers (For pairs ETH and BTC)
# on the given side.
# By default attempts to cancel all nonzero balance coins.
# Pass in multiple tickers separated by commas, ex:
#   cancel_all_orders('TRX', 'ADA', 'ICX')
def cancel_all_orders(*tickers, side='both'):
    tickers = tickers if len(tickers) > 0 else get_nonzero_balances().keys()
    for ticker in tickers:
        cancel_orders(ticker, side)


# Returns the usd balance of the ticker.
def get_usd_balance(ticker):
    if ticker in ('USDT', 'USD'):
        return 1
    balance = get_balance(ticker, 'total')
    pairs = set(symbol.split('/')[1] for symbol in exchange.symbols)
    for pair in pairs:
        symbol = f'{ticker}/{pair}'
        if symbol in exchange.symbols:
            if f'{pair}/USDT' in exchange.symbols:
                pair_usd = get_symbol(f'{pair}/USDT')['ask']
                return pair_usd * balance * get_symbol(symbol)['ask']


# Returns the equivalent USD amount of all cryptos in the account.
def get_portfolio():
    balances = get_nonzero_balances()
    usd_balances = {ticker: get_usd_balance(ticker) for ticker in balances.keys()}
    total = sum(usd_balances.values())
    portfolio = {'total': total}
    for ticker in usd_balances.keys():
        portfolio[ticker] = {}
        portfolio[ticker]['total'] = round(usd_balances[ticker], 2)
        portfolio[ticker]['percent'] = round(usd_balances[ticker]/total*100, 2)
    return portfolio
