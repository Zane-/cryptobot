from math import floor
from time import sleep

from auth import *


# Exception decorator to retry functions upon ccxt exceptions
def retry_on_exception(timeout, retries=10):
    def decorator(func):
        def wrapper(*args, **kwargs):
            for _ in range(retries):
                try:
                    return func(*args, **kwargs)
                except (ccxt.NetworkError, ccxt.ExchangeError) as e:
                    print(e)
                    sleep(timeout)
                    continue
            print(f'{func.__name__} failed to execute after {retries} retries.')
            return None
        return wrapper
    return decorator


# Returns the balance of the ticker in the account.
@retry_on_exception(2)
def fetch_balance(ticker, account='free'):
    return float(exchange.fetch_balance()[ticker][account])


# Returns a list of tickers with non-zero balances (at least 1) in the account.
# Does not list ETH or BTC (unless they are over 1).
@retry_on_exception(2)
def fetch_nonzero_balances():
    balances = exchange.fetch_balance()['total']
    return [ticker for ticker in balances.keys() if balances[ticker] >= 1]


# Returns data for the ticker.
@retry_on_exception(2)
def fetch_ticker(ticker, pair='ETH'):
    data = exchange.fetch_ticker(ticker + f'/{pair}')
    return {'bid': float(data['bid']),           'change': float(data['change']),
            'high': float(data['high']),         'low': float(data['low']),
            'volume': float(data['baseVolume']), 'last': float(data['last'])}


# Returns a dictionary w/ the prices and percent changes of all cryptos passed in.
def fetch_tickers(tickers, pair='ETH'):
    return {ticker: fetch_ticker(ticker, pair) for ticker in tickers}


# Places a market sell order for the ticker using the
# given percentage of the available balance.
@retry_on_exception(2)
def sell(ticker, percent, pair='ETH'):
    order = exchange.create_market_sell_order(
                ticker + f'/{pair}',
                floor(fetch_balance(ticker) * (percent/100)))
    return order


# Places a limit sell order for the ticker using the
# given percentage of the available balance.
@retry_on_exception(2)
def limit_sell(ticker, percent, price, pair='ETH'):
    order = exchange.create_limit_sell_order(
        ticker + f'/{pair}',
        floor(fetch_balance(ticker) * (percent/100)),
        price)
    return order


# Places a market sell order for each of the tickers at the given percentage of
# the total balance.
def sell_tickers(tickers, percent, pair='ETH'):
    for ticker in data:
        sell(ticker, percent, pair)


# Places a market buy order for the ticker using the specified percentage of the pair
# currency. If the order does not go through, an another is placed for 1% less volume.
def buy(ticker, percent, pair='ETH'):
    amount = floor(fetch_balance(pair) * (percent/pair) / fetch_ticker(ticker)['bid'])
    bought = False
    while not bought:
        try:
            order = exchange.create_market_buy_order(ticker + f'/{pair}', amount)
        except ccxt.InsufficientFunds as e:
            amount *= 0.99 # step down by 1% until order placed
            continue
        except ccxt.NetworkError as e:
            print(e)
            continue
        except ccxt.ExchangeError as e:
            print(e)
            return None
        bought = True
    return order


# Places a limit buy order for the ticker. If the order does
# not go through, another is placed for 1% less volume.
def limit_buy(ticker, amount, price, pair='ETH'):
    buy_placed = False
    while not buy_placed:
        try:
            order = exchange.create_limit_buy_order(
                ticker + f'/{pair}',
                amount,
                price)
        except ccxt.InsufficientFunds as e:
            amount *= 0.99 # step down by 1% until order placed
            continue
        except ccxt.NetworkError as e:
            print(e)
            continue
        except ccxt.ExchangeError as e:
            print(e)
            return None
        buy_placed = True
    return order


# Places a market buy order for each of the cryptos in the data with
# an equal amount of ether.
def buy_tickers(tickers, pair='ETH'):
    pair_per = fetch_balance(pair) / len(tickers)
    for ticker in tickers:
        buy(ticker, fetch_ticker(ticker)['bid'], pair_per, pair)


# Swaps a given percentage of one currency into another at market.
def swap(this, that, percent, pair='ETH'):
    order = sell(this, percent, pair)
    pair_amount = order['origQty'] * order['price']
    pair_percent = 100 * (pair_amount / fetch_balance(pair))
    return buy(that, pair_percent, pair)


# Swaps a given percentage of this for that. Sells this at the given percentage increase
# and buys that at the given percentage decrease.
def swap_limit(this, that, percentage, this_increase, that_decrease, pair='ETH'):
    order = limit_sell(this, percentage, fetch_ticker(this)['bid'] * (that_increase/100), pair)
    pair_amount = order['origQty'] * order['price']
    buy_price = fetch_ticker(that)['bid'] * (100-that_decrease/100)
    buy_amount = pair_amount / buy_price
    limit_buy(that, buy_amount, buy_price, pair)


# Cancels an order given the order id, ticker, and pair.
@retry_on_exception(2)
def cancel_order(order_id, ticker, pair='ETH'):
    exchange.cancel_order(order_id, ticker + f'/{pair}')


# Cancels all open orders for the given ticker.
def cancel_open_orders(ticker, pair='ETH'):
    for order in exchange.fetch_open_orders(ticker + f'/{pair}'):
        cancel_order(order['info']['orderId'], ticker), pair


# Cancels all open orders for the given tickers.
# By default attempts to cancel all nonzero balance coins.
def cancel_all_orders(tickers=None, pair='ETH'):
    tickers = tickers if tickers is not None else fetch_nonzero_balances()
    for ticker in tickers:
        cancel_open_orders(ticker, pair)


# Returns the usd balance of the ticker.
def get_usd_balance(ticker, pair='ETH'):
    pair_usd = fetch_ticker(pair, 'USDT')['last']
    return pair_usd * fetch_balance(ticker, 'total') * fetch_ticker(ticker, pair)['last']


# Returns the equivalent USD amount of all cryptos in the account.
def get_portfolio():
    eth_usd = fetch_ticker('ETH', 'USDT')['last']
    eth_total = fetch_balance('ETH') * eth_usd
    btc_usd = fetch_ticker('BTC', 'USDT')['last']
    btc_total = fetch_balance('BTC') * btc_usd
    total = eth_total + btc_total + fetch_balance('USDT')
    balances = fetch_nonzero_balances()
    if 'ETH' in balances: balances.remove('ETH')
    if 'BTC' in balances: balances.remove('BTC')
    if 'USDT' in balances: balances.remove('USDT')
    return total + sum(get_usd_balance(ticker) for ticker in balances)


# Places a market sell order for the full amount of each of the cryptos in WATCHING.
# Used to redistrubute total funds into all cryptos when distribution becomes too skewed.
def normalize_balances(pair='ETH'):
    tickers = fetch_nonzero_balances()
    sell_tickers(tickers, 100, pair)
    buy_tickers(tickers, pair)
