import re
from math import ceil, floor, modf
from time import sleep

from auth import *

# Minimum amount requirements for transactions on Binance.
MINIMUM_AMOUNTS = {
    'ETH': 0.01,
    'BTC': 0.001,
    'BNB': 1
}

# Exception decorator to retry functions upon ccxt exceptions
def retry_on_exception(timeout, retries=3):
    def decorator(func):
        def wrapper(*args, **kwargs):
            for _ in range(retries):
                try:
                    return func(*args, **kwargs)
                except ccxt.NetworkError as e:
                    print(e)
                    sleep(timeout)
                    continue
                except ccxt.ExchangeError as e:
                    print(e)
                    return None
            print(f'{func.__name__} failed to execute after {retries} retries.')
            return None
        return wrapper
    return decorator


# Returns the balance of the ticker in the account.
@retry_on_exception(2)
def get_balance(ticker, account='free'):
    return float(exchange.fetch_balance()[ticker][account])


# Returns a list of tickers with non-zero balances in the account.
# Does not list ETH, BTC, BNB, or USDT.
@retry_on_exception(2)
def get_nonzero_balances(pairs=True):
    balances = exchange.fetch_balance()['total']
    if not pairs:
        balances.pop('ETH', None)
        balances.pop('BTC', None)
        balances.pop('USDT', None)
        balances.pop('BNB', None)
    return {asset: balances[asset] for asset in balances.keys() if balances[asset] > 0}


# Returns data for the ticker.
# Fractional returns whether or not the ticker can be sold in fractional amounts.
@retry_on_exception(2)
def get_ticker(ticker, pair='ETH'):
    data = exchange.fetch_ticker(ticker + f'/{pair}')
    return {'bid': data['bid'],           'change': data['change'],
            'high': data['high'],         'low': data['low'],
            'volume': data['baseVolume'], 'last': data['last'],
            'fractional': modf(float(data['info']['lastQty']))[0] > 0}


# Returns a dictionary w/ ticker data for each ticker passed in.
def get_tickers(tickers, pair='ETH'):
    return {ticker: get_ticker(ticker, pair) for ticker in tickers}


# Places a market sell order for the ticker using the
# given percentage of the available balance.
@retry_on_exception(2)
def sell(ticker, pair, percentage, price='market', *, auto_adjust=False):
    symbol = ticker + f'/{pair}'
    ticker_data = get_ticker(ticker, pair)
    ticker_balance = get_balance(ticker)

    if price == 'market':
        price = ticker_data['last']

    amount = ticker_balance * (percentage/100)
    if not ticker_data['fractional']:
        amount = floor(amount)


    sell_total = amount * price
    if sell_total < MINIMUM_AMOUNTS[pair]:
        min_amount = MINIMUM_AMOUNTS[pair] / price
        if not ticker_data['fractional']:
            min_amount = ceil(min_amount)

        if min_amount <= ticker_balance and auto_adjust:
                amount = min_amount
        else:
            min_percentage = min_amount / ticker_balance * 100
            print((f'Order total does not meet minimum requirement of {MINIMUM_AMOUNTS[pair]} {pair}. '
                   f'{min_percentage:.3f}% is the minimum needed. Pass in auto_adjust=True to attempt '
                   f'to automatically adjust to this percent.'))
            return None

    if price == 'market':
        return exchange.create_market_sell_order(symbol, amount)
    else:
        return exchange.create_limit_sell_order(symbol, amount, price)


# Places a market sell order for each of the tickers at the given percentage of
# the total balance.
def sell_tickers(tickers, pair, percentage, price='market', *, auto_adjust=False):
    return [sell(ticker, pair, percentage, price, auto_adjust=auto_adjust) for ticker in tickers]


# Places a market sell order for the ticker using the
# given percentage of the available balance.
@retry_on_exception(2)
def buy(ticker, pair, percentage, price='market', *, auto_adjust=False):
    symbol = ticker + f'/{pair}'
    ticker_data = get_ticker(ticker)
    price = ticker_data['last']
    pair_balance = get_balance(pair)
    pair_amount = pair_balance * (percentage/100)

    amount = pair_amount / price
    if pair_amount < MINIMUM_AMOUNTS[pair]:
        if auto_adjust:
            amount = MINIMUM_AMOUNTS[pair] / price
            if not ticker_data['fractional']:
                amount = floor(amount) + 1
        else:
            min_percentage = MINIMUM_AMOUNTS[pair] / pair_balance * 100
            print((f'Order total does not meet minimum requirement of {MINIMUM_AMOUNTS[pair]} {pair}. '
                   f'{min_percentage:.3f}% is the minimum needed. Pass in auto_adjust=True to attempt '
                   f'to automatically adjust to this percent.'))
            return None
    else:
        if not ticker_data['fractional']:
            amount = ceil(amount) # round up to avoid rounding below minimum

    if price == 'market':
        return exchange.create_market_buy_order(symbol, amount)
    else:
        return exchange.create_limit_buy_order(symbol, amount, price)


# Places a market buy order for each of the tickers at the given percentage of
# the total pair balance.
def buy_tickers(tickers, pair, percentage, price='market', *, auto_adjust=False):
    return [buy(ticker, pair, percentage, price, auto_adjust=auto_adjust) for ticker in tickers]


# Swaps a given percentage of one currency into another at market.
def swap(this, that, pair, percentage, *, auto_adjust=False):
    sell = sell(this, pair, percentage, auto_adjust=auto_adjust)
    pair_amount = sell['info']['origQty'] * sell['info']['price']
    pair_percentage = pair_amount / get_balance(pair) * 100
    buy = buy(that, pair, pair_amount / get_balance(pair) * 100, auto_adjust=auto_adjust)
    return [sell, buy]


# Swaps a given percentage of this for that. Sells this at the given percentage increase
# and buys that at the given percentage decrease.
def swap_limit(this, that, pair, percentage, this_increase, that_decrease, *, auto_adjust=False):
    sell_price = get_ticker(this)['bid'] * (100+that_increase/100)
    sell = sell(this, pair, percentage, sell_price, auto_adjust=auto_adjust)
    pair_amount = sell['info']['origQty'] * sell['info']['price']
    pair_percentage = pair_amount / get_balance(pair) * 100
    buy_price = get_ticker(that)['bid'] * (100-that_decrease)/100
    buy = buy(that, pair, pair_percantage, buy_price, auto_adjust=auto_adjust)
    return [sell, buy]


# Cancels an order given the order dictionary.
#
@retry_on_exception(2)
def cancel_order(order, *, order_id=None, symbol=None):
    symbol = order['info']['symbol'][::-1] # reverse to extract pair as first group
    # symbol_regex = re.compile(r'(\w+)(BTC|ETH|BNB|USDT)')
    symbol_regex = re.compile(r'(TDSU|BNB|HTE|CTB)(\w+)')
    match = symbol_regex.match(symbol)
    if match:
        print(match)                       # reverse the symbol back
        exchange.cancel_order(order['id'], match[1][::-1] + f'/{match[0][::-1]}')
    return False


# Cancels all open orders for the given ticker.
def cancel_open_orders(ticker):
    symbols = [ticker + f'/BTC', ticker + f'/ETH', ticker + f'/BNB', ticker + f'/USDT']
    for symbol in symbols:
        if symbol in exchange.symbols:
            for order in exchange.fetch_open_orders(symbol):
                cancel_order(order)


# Cancels all open orders for the given tickers (For pairs ETH and BTC).
# By default attempts to cancel all nonzero balance coins.
# Pass in multiple tickers separated by commas, example:
#   cancel_all_orders('TRX', 'ADA', 'ICX')
def cancel_all_orders(*tickers):
    tickers = tickers if len(tickers) > 0 else get_nonzero_balances(pairs=False).keys()
    for ticker in tickers:
        cancel_open_orders(ticker)


# Returns the usd balance of the asset.
def get_usd_balance(asset):
    balance = get_balance(asset, 'total')
    if asset + '/BTC' in exchange.symbols:
        btc_usd = get_ticker('BTC', 'USDT')['last']
        return get_ticker(asset, 'BTC')['last'] * balance * btc_usd
    elif asset + '/ETH' in exchange.symbols:
        eth_usd = get_ticker('ETH', 'USDT')['last']
        return get_ticker(asset, 'ETH')['last'] * balance * eth_usd
    elif asset + '/BNB' in exchange.symbols:
        bnb_usd = get_ticker('BNB', 'USDT')['last']
        return get_ticker(asset, 'BNB')['last'] * balance * bnb_usd
    elif asset + '/USDT' in exchange.symbols:
        return get_ticker(asset, 'USDT')['last'] * balance
    elif asset == 'USDT':
        return balance
    else:
        return -1 # ticker not found value


# Returns the equivalent USD amount of all cryptos in the account.
def get_portfolio():
    balances = get_nonzero_balances()
    usd_balances = {asset: get_usd_balance(asset) for asset in balances.keys()}
    total = sum(usd_balances.values())
    portfolio = {'total': total}
    for asset in usd_balances.keys():
        portfolio[asset] = {}
        portfolio[asset]['total'] = round(usd_balances[asset], 2)
        portfolio[asset]['percent'] = round(usd_balances[asset]/total*100, 2)
    return portfolio


# ### DUSTING FUNCTIONS ###
# # These should be temporary, as Binance is apparently in the works of adding
# # this to their exchange.

# # Converts a ticker to BNB.
# def convert_to_bnb(ticker):
#     if ticker + '/BNB' in exchange.symbols:
#         return get_balance(ticker, 'total') * get_ticker(ticker, 'BNB')['last']


# # Returns a dictionary with all tickers that contain non-fractional balances
# with the non-fractional part
# def find_dust():
#     balances = exchange.get_balance()['total']
#     balances.pop('ETH', None)
#     balances.pop('BTC', None)
#     balances.pop('USDT', None)
#     balances.pop('BNB', None)
#     # return all tickers with non-integer values
#     return [ticker for ticker in balances if modf(balances[ticker])[0] > 0.01]


# # Sells coins with a fractional value into BNB
# def clean_dust():
#     dust = find_dust()
#     for ticker in dust:
#         if ticker + '/BNB' in exchange.symbols:
#             bnb_value = convert_to_bnb(ticker)
#         else:
#             continue
#         if bnb_value > 1:
#             sell(ticker, 100, 'BNB')
#         else:
#             ticker_needed = 1 - get_balance(ticker) + 0.01 # ROUNDING ERRORS :(
#             try:
#                 order = exchange.create_market_buy_order(ticker + '/BNB', ticker_needed)
#             except ccxt.BaseError as e:
#                 print(e)
#                 continue
#             print(order)
#             sell(ticker, 100, 'BNB')

