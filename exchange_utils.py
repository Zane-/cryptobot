import re
from math import ceil, floor, modf
from time import sleep

from auth import *


# Always rounds a floating number up to the specified precision.
# Ex. round_up(12.344, 3) -> 12.345
def round_up(n, precision):
    x = 10**-precision
    return round(ceil(n/x)*x, precision)


# Always rounds a floating number down to the specified precision.
# Ex. round_up(12.346, 2) -> 12.34
def round_down(n, precision):
    x = 10**-precision
    return round(floor(n/x)*x, precision)


# Exception decorator to retry functions upon ccxt NetworkErrors.
def retry_on_exception(interval, retries=3):
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


# Returns a dictionary w/ data on all symbols on the exchange.
def get_all_tickers():
    data = exchange.fetch_tickers()
    tickers = {}
    for ticker in data:
        tickers[ticker] = {}
        tickers[ticker]['bid'] = data[ticker]['bid']
        tickers[ticker]['change'] = data[ticker]['change']
        tickers[ticker]['high'] = data[ticker]['high']
        tickers[ticker]['low'] = data[ticker]['low']
        tickers[ticker]['volume'] =  data[ticker]['quoteVolume']
        tickers[ticker]['last'] = data[ticker]['last']
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
    price = get_ticker(ticker)['bid'] if price == 'market' else price
    amount = round_down(get_balance(ticker) * percentage/100, precision)
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
    pair_amount = round_down(get_balance(pair) * percentage/100, precision)
    price = get_ticker(ticker)['bid'] if price == 'market' else price
    amount = pair_amount / price
    min_amount = round_up(pair_min / price, precision)

    if amount < min_amount:
        if auto_adjust:
            amount = min_amount
        else:
            raise ccxt.InvalidOrder(f'Order does not meet minimum requirement of {pair_min} {pair}')

    if amount * price > get_balance(pair):
        raise ccxt.InsufficientFunds('Insufficient funds to place this order')

    if price == 'market':
        return exchange.create_market_buy_order(symbol, amount)
    else:
        return exchange.create_limit_buy_order(symbol, amount, price)


# Swaps a given percentage this into that at market. This and that must
# share a common pair.
def swap(this, that, pair, percentage_this, *, auto_adjust=True):
    if not (f'{this}/{pair}' and f'{that}/{pair}') in exchange.symbols:
        raise ccxt.ExchangeError(f'{this} and {that} do not share the pair {pair}.')
    sell_order = sell(this, pair, percentage_this, auto_adjust=auto_adjust)

    pair_amount = sell_order['info']['origQty'] * sell['info']['price']
    pair_percentage = pair_amount / get_balance(pair) * 100

    buy_order = buy(that, pair, pair_percentage, auto_adjust=auto_adjust)
    return (sell_order, buy_order)


# Returns all open orders for the ticker passed in. Returns a dictionary divided
# into lists for buy and sell orders.
@retry_on_exception(2)
def get_open_orders(ticker):
    orders = {'buy': [], 'sell': []}
    symbols = [ticker + f'/BTC', ticker + f'/ETH', ticker + f'/BNB', ticker + f'/USDT']
    for symbol in symbols:
        if symbol in exchange.symbols:
            for order in exchange.fetch_open_orders(symbol):
                orders[order['side']].append(order)
    return orders


# Cancels an order given the order dictionary returned by buy/sell.
@retry_on_exception(2)
def cancel(order):
    symbol = order['info']['symbol']
    symbol_regex = re.compile(r'(\w+)(BTC|ETH|BNB|USDT)')
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
    tickers = tickers if len(tickers) > 0 else get_nonzero_balances(pairs=False).keys()
    for ticker in tickers:
        cancel_orders(ticker, side)


# Returns the usd balance of the asset.
def get_usd_balance(asset):
    balance = get_balance(asset, 'total')
    if f'{asset}/BTC' in exchange.symbols:
        btc_usd = get_ticker('BTC', 'USDT')['last']
        return get_ticker(asset, 'BTC')['last'] * balance * btc_usd
    elif f'{asset}/ETH' in exchange.symbols:
        eth_usd = get_ticker('ETH', 'USDT')['last']
        return get_ticker(asset, 'ETH')['last'] * balance * eth_usd
    elif f'{asset}/BNB' in exchange.symbols:
        bnb_usd = get_ticker('BNB', 'USDT')['last']
        return get_ticker(asset, 'BNB')['last'] * balance * bnb_usd
    elif f'{asset}/USDT' in exchange.symbols:
        return get_ticker(asset, 'USDT')['last'] * balance
    elif asset == 'USDT':
        return balance
    else:
        return -1 # asset not found


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
