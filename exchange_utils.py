import re
from math import ceil, floor, modf
from time import sleep

from auth import *


# Always rounds a floating number up to the specified digits.
# Ex. round_up(12.344, 3) -> 12.345
def round_up(n, digits):
    x = 10**-digits
    return round(ceil(n/x)*x, digits)


# Exception decorator to retry functions upon ccxt NetworkErrors.
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
# Note: Fractional can return an incorrect value if a ticker that allows fractional
# amounts was last traded at a whole value. This can cause undesirable results if
# the buy finds the ticker is non-fractional and rounds up to the next value, which
# can potentially result in buying 1 LTC instead of 0.01.
@retry_on_exception(2)
def get_ticker(ticker, pair='ETH'):
    data = exchange.fetch_ticker(f'{ticker}/{pair}')
    return {'bid': data['bid'],            'change': data['change'],
            'high': data['high'],          'low': data['low'],
            'volume': data['quoteVolume'], 'last': data['last']}


# Returns a dictionary w/ ticker data for each ticker passed in.
def get_tickers(tickers, pair='ETH'):
    return {ticker: get_ticker(ticker, pair) for ticker in tickers}


# Returns a dictionary w/ data on all symbols on the exchange.
# TODO: exchange.fetch_tickers() is way faster, use this and then just
# prune it for the keys you want.
def get_all_tickers():
    tickers = {}
    for symbol in exchange.symbols:
        ticker, pair = symbol.split('/')
        tickers[symbol] = get_ticker(ticker, pair)
    return tickers


# Places a sell order for the ticker and pair using the given percentage of the ticker.
# Pass in a price for the price parameter to post a limit order.
# auto_adjust sets the amount as the minimum amount if the minimum amount is not reached.
@retry_on_exception(2)
def sell(ticker, pair, percentage, price='market', *, auto_adjust=False):
    symbol = f'{ticker}/{pair}'.upper()
    precision = exchange_config['precision'][symbol]
    pair_min = exchange_config['MINIMUM_AMOUNTS'][pair]
    # round down to the precision required
    amount = round_down(get_balance(ticker) * percentage/100, precision)

    if price == 'market':
        min_amount = round_up(pair_min / get_ticker(ticker)['bid'], precision)
    else:
        min_amount = round_up(pair_min / price, precision)

    if amount < min_amount:
        if auto_adjust:
            amount = min_amount
        else:
            raise ccxt.InvalidOrder(f'Order does not meet minimum requirement of {pair_min} {pair}')

    if amount > get_balance(ticker):
        raise ccxt.InsufficientFunds('Insufficient funds to place this order')

    if price == 'market':
        return exchange.create_market_sell_order(symbol, amount)
    else:
        return exchange.create_limit_sell_order(symbol, amount, price)


# Places a buy order for the ticker and pair using the given percentage of the ticker.
# Pass in a price for the price parameter to post a limit order.
# auto_adjust sets the amount as the minimum amount if the minimum amount is not reached.
@retry_on_exception(2)
def buy(ticker, pair, percentage, price='market', *, auto_adjust=False):
    symbol = f'{ticker}/{pair}'.upper()
    precision = exchange_config['precision'][symbol]
    pair_min = exchange_config['MINIMUM_AMOUNTS'][pair]
    # round down to the precision required
    amount = round_down(get_balance(ticker) * percentage/100, precision)
    bid = get_ticker(ticker)['bid']

    if price == 'market':
        min_amount = round_up(pair_min / bid, precision)
    else:
        min_amount = round_up(pair_min / price, precision)

    if amount < min_amount:
        if auto_adjust:
            amount = min_amount
        else:
            raise ccxt.InvalidOrder(f'Order does not meet minimum requirement of {pair_min} {pair}')

    if amount * bid > get_balance(pair):
        raise ccxt.InsufficientFunds('Insufficient funds to place this order')

    if price == 'market':
        return exchange.create_market_buy_order(symbol, amount)
    else:
        return exchange.create_limit_buy_order(symbol, amount, price)


# Swaps a given percentage of one currency into another at market.
def swap(this, that, pair, percentage, *, auto_adjust=False):
    sell = sell(this, pair, percentage, auto_adjust=auto_adjust)
    pair_amount = sell['info']['origQty'] * sell['info']['price']
    pair_percentage = pair_amount / get_balance(pair) * 100
    buy = buy(that, pair, pair_amount / get_balance(pair) * 100, auto_adjust=auto_adjust)
    return (sell, buy)


# Swaps a given percentage of this for that. Sells this at the given percentage increase
# and buys that at the given percentage decrease.
def swap_limit(this, that, pair, percentage, this_increase, that_decrease, *, auto_adjust=False):
    sell_price = get_ticker(this)['bid'] * (100+that_increase/100)
    sell = sell(this, pair, percentage, sell_price, auto_adjust=auto_adjust)

    pair_amount = sell['info']['origQty'] * sell['info']['price']
    pair_percentage = pair_amount / get_balance(pair) * 100

    buy_price = get_ticker(that)['bid'] * (100-that_decrease)/100
    buy = buy(that, pair, pair_percantage, buy_price, auto_adjust=auto_adjust)
    return (sell, buy)


# Cancels an order given the order dictionary returned by buy/sell.
@retry_on_exception(2)
def cancel_order(order):
    symbol = order['info']['symbol']
    symbol_regex = re.compile(r'(\w+)(BTC|ETH|BNB|USDT)')
    match = symbol_regex.match(symbol)
    if match:
        exchange.cancel_order(order['id'], match[1] + f'/{match[2]}')
        return True
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
