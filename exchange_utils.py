import re
from functools import wraps
from math import floor, ceil
from time import sleep

from auth import *


def network_error_retry(interval, retries=5):
    """Decorator to retry functions on ccxt NetworkErrors.

    Add @network_error_retry(interval) directly above a function declaration to use.

    Args:
        interval: The seconds to sleep between retries.
            Use at least 1 second to avoid spamming the API with responses.
        retries: The number of times to retry. Defaults to 5.
    """
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            for _ in range(retries):
                try:
                    return func(*args, **kwargs)
                except ccxt.NetworkError:
                    print(f'A network error occured. Retrying in {interval} seconds.')
                    sleep(interval)
            return None
        return wrapper
    return decorator


@network_error_retry(2)
def get_balance(ticker, account='free'):
    """Gets the balance for a ticker using the specified account.

    Args:
        ticker: The ticker to get the balance for.
        account: The account to get the balance for. Can either be
            'free', returning the balance not in open trades, etc.,
            or 'total', returning the balance including open trades, etc.
            Defaults to 'free'.

    Returns:
        A float of the balance of the ticker in the specified account.
    """
    return exchange.fetch_balance()[ticker][account]


@network_error_retry(2)
def get_nonzero_balances(account='total'):
    """Gets the nonzero balances in the account.

    Args:
        account: The account to get the balance for. Can either be
            'free', returning the balance not in open trades, etc.,
            or 'total', returning the balance including open trades, etc.
            Defaults to 'total'.

    Returns:
        A dictionary mapping each nonzero asset to its balance in the
        specified account.
    """
    balances = exchange.fetch_balance()[account]
    return {ticker: balances[ticker] for ticker in balances if balances[ticker] > 0}


@network_error_retry(2)
def get_symbol(symbol):
    """Gets market data on the symbol.

    Args:
        symbol: The symbol to fetch. Example: get_symbol('XLM/ETH').

    Returns:
        A dictionary mapping each attribute to current market data.
        Includes bid, ask, last, open, close, high, low, change, and volume.
    """
    return exchange.fetch_ticker(symbol)


def get_symbols(*symbols):
    """Returns a dictionary mapping each symbol passed in to its market data."""
    return {symbol: get_symbol(symbol) for symbol in symbols}


@network_error_retry(2)
def get_all_symbols():
    """Returns a dictionary mapping all symbols in the exchange to their market data."""
    data = exchange.fetch_tickers() # returns data for all symbols
    symbols = {}
    for symbol in data:
        symbols[symbol] = {key: data[symbol][key] for key in data[symbol]}
    return symbols


# rounds down a float to the specified precision: round_down(12.3556, 3) -> 12.355
round_down = lambda n, p: round(floor(n/10**-p)*10**-p, p)
# rounds up a float to the specified precision: round_up(12.3543, 3) -> 12.355
round_up = lambda n, p: round(ceil(n/10**-p)*10**-p, p)


@network_error_retry(1)
def sell(symbol, percentage, price='market', *, auto_adjust=False):
    """Places a sell order.

    Args:
        symbol: The symbol to sell.
        percentage: The percentage of the symbol to sell.
        price: The price to sell at. Defaults to 'market' (the lowest ask).
        auto_adjust: Whether or not to automatically set the percentage
            to the minimum if it is not met through the original parameters
            passed in. Defaults to False. Must be passed in as a keyword arg.

    Returns:
        A dictionary containing the JSON response returned by the exchange.
        Will vary between exchanges.
        Example (Binance):
            {
                'id': '11204430',
                'info': {
                    'clientOrderId': 'xLl6oDWCIBFd5bmCml62Xp',
                    'executedQty': '0.00000000',
                    'orderId': 11204430,
                    'origQty': '0.93000000',
                    'price': '0.05000000',
                    'side': 'SELL',
                    'status': 'NEW',
                    'symbol': 'BNBETH',
                    'timeInForce': 'GTC',
                    'transactTime': 1515689255908,
                    'type': 'LIMIT'
                }
            }

    Raises:
        ccxt.InvalidOrder: The order was invalid: price too high/low, amount too high/low, cost too high/low.
        ccxt.InsufficientFunds: There was not enough funds in the balance of the symbol to place the order.
    """
    ticker, pair = symbol.upper().split('/')
    limits = exchange.markets[symbol]['limits']
    precision = exchange.markets[symbol]['precision']['amount']

    sell_price = get_symbol(symbol)['bid'] if price == 'market' else float(exchange.price_to_precision(symbol, price))
    ticker_balance = get_balance(ticker)
    # round down amount to avoid api auto rounding the wrong way, causing an insufficient funds exception
    amount = round_down(ticker_balance * percentage/100, precision)
    min_pair = limits['cost']['min']
    # round up amount to avoid api auto rounding the wrong way, causing an invalid order exception
    min_amount = round_up(min_pair / sell_price, precision)

    if amount < min_amount:
        if auto_adjust:
            amount = min_amount
        else:
            raise ccxt.InvalidOrder(f'Order does not meet minimum requirement of {min_pair} {pair}')
    if amount > ticker_balance:
        raise ccxt.InsufficientFunds(f'Account does not have {amount} {ticker}. Balance: {ticker_balance}')

    if price == 'market':
        return exchange.create_market_sell_order(symbol, amount)
    else:
        return exchange.create_limit_sell_order(symbol, amount, price)


@network_error_retry(1)
def buy(symbol, percentage, price='market', *, auto_adjust=False):
    """Places a buy order.

    Args:
        symbol: The symbol to buy.
        percentage: The percentage of the symbol to buy with.
            Example: buy('XLM/ETH', 50) will buy XLM using 50%
                of the available ETH balance.
        price: The price to buy at. Defaults to 'market' (the lowest ask).
        auto_adjust: Whether or not to automatically set the percentage
            to the minimum if it is not met through the original parameters
            passed in. Defaults to False. Must be passed in as a keyword arg.

    Returns:
        A dictionary containing the JSON response returned by the exchange.
        Will vary between exchanges.
        Example (Binance):
            {
                'id': '11204430',
                'info': {
                    'clientOrderId': 'xLl6oDWCIBFd5bmCml62Xp',
                    'executedQty': '0.00000000',
                    'orderId': 11204430,
                    'origQty': '0.93000000',
                    'price': '0.05000000',
                    'side': 'BUY',
                    'status': 'NEW',
                    'symbol': 'BNBETH',
                    'timeInForce': 'GTC',
                    'transactTime': 1515689255908,
                    'type': 'LIMIT'
                }
            }

    Raises:
        ccxt.InvalidOrder: The order was invalid: price too high/low, amount too high/low, cost too high/low.
        ccxt.InsufficientFunds: There was not enough funds in the balance of the symbol to place the order.
    """
    ticker, pair = symbol.upper().split('/')
    limits = exchange.markets[symbol]['limits']
    precision = exchange.markets[symbol]['precision']['amount']

    buy_price = get_symbol(symbol)['ask'] if price == 'market' else float(exchange.price_to_precision(symbol, price))
    pair_balance = get_balance(pair)
    pair_amount = pair_balance * percentage/100
    # round down amount to avoid api auto rounding the wrong way, causing an insufficient funds exception
    amount = round_down(pair_amount / buy_price, precision)
    # round up amount to avoid api auto rounding the wrong way, causing an invalid order exception
    min_pair = limits['cost']['min']
    min_amount = round_up(min_pair / buy_price, precision)

    if amount < min_amount:
        if auto_adjust:
            amount = min_amount
        else:
            raise ccxt.InvalidOrder(f'Order does not meet minimum requirement of {min_pair} {pair}')
    if amount * buy_price > pair_balance:
        raise ccxt.InsufficientFunds(f'Account does not have {amount} {ticker}. Balance: {ticker_balance}')
    if price == 'market':
        return exchange.create_market_buy_order(symbol, amount)
    else:
        return exchange.create_limit_buy_order(symbol, amount, buy_price)


def swap(this, that, percentage, *, auto_adjust=False):
    """Swaps two symbols at market price.

    Args:
        this: The symbol to sell.
        that: The symbol to buy.
        percentage: The percentage of 'this' to sell.
        auto_adjust: Whether or not to automatically set the percentage
            to the minimum if it is not met through the original parameters
            passed in. Defaults to False. Must be passed in as a keyword arg.

    Returns:
        A tuple containing the JSON responses of the sell and buy orders respectively.
    """
    sell_price = get_symbol(this)['ask']  # get ask because market orders don't return price
    sell_order = sell(this, percentage, auto_adjust=auto_adjust)

    pair_amount = sell_order['info']['origQty'] * sell_price
    pair_percentage = pair_amount / get_balance(pair) * 100

    buy_order = buy(that, pair_percentage, auto_adjust=auto_adjust)
    return (sell_order, buy_order)


def limit_swap(this, that, percentage, this_price, that_price, *, wait_til_filled=True, auto_adjust=False):
    """Swaps two symbols at a given price for both.

    Args:
        this: The symbol to sell.
        that: The symbol to buy.
        percentage: The percentage of 'this' to sell.
        wail_til_filled: Whether or not to wait until the sell order has been
            completely filled before placing the buy order.
            Defaults to True. Must be passed in as a keyword arg.
        auto_adjust: Whether or not to automatically set the percentage
            to the minimum if it is not met through the original parameters
            passed in. Defaults to False. Must be passed in as a keyword arg.
    """
    sell_order = sell(this, percentage, this_price, auto_adjust=auto_adjust)

    if wait_til_filled:
        while exchange.fetch_order(sell_order['id'], this)['status'] != 'filled':
            sleep(3)  # check for order fill every 3 seconds to avoid spamming api

    pair_amount = sell_order['info']['origQty'] * sell_order['info']['price']
    pair_percentage = pair_amount / get_balance(pair) * 100

    buy_order = buy(that, pair_percentage, auto_adjust=auto_adjust)
    return (sell_order, buy_order)


@network_error_retry(2)
def get_open_orders(ticker):
    """Returns open orders for the ticker.

    Will get open orders for all symbols containing the ticker in the first
    half of the symbol.
        Example: get_open_order('XLM') will get orders for symbols 'XLM/ETH'
            and 'XLM/BTC', but not 'BNB/XLM' (if it exists).

    Args:
        ticker: The ticker to fetch open orders for.

    Returns:
        A dictionary mapping a list of open buy orders to 'buy' and a
        list of open sell orders to 'sell'.
    """
    orders = {'buy': [], 'sell': []}
    symbols = [symbol for symbol in exchange.symbols if symbol.startswith(ticker)]
    for symbol in symbols:
        for order in exchange.fetch_open_orders(symbol):
            orders[order['side']].append(order)
    return orders


@network_error_retry(2)
def cancel(order):
    """Cancels an order given the JSON response from the order.

    Because different exchanges give differently structured JSON
    responses, the ccxt parsed response (from get_open_orders)
    should be used. If the ccxt response is not passed in, attempts
    to parse the symbol.

    Args:
        order: The dictionary containing the order information.

    Returns:
        True of the order was canceled, False if not.
    """
    # try to use the ccxt parsed response if it was passed in
    symbol = order.pop('symbol', None)
    if symbol is None:
        # attempt to parse the symbol from the JSON response
        symbol = order['info']['symbol']
        # unified representation of symbols for ccxt
        pairs = set(symbol.split('/')[1] for symbol in exchange.symbols)
        pairs_regex = '|'.join(pairs)
        symbol_regex = re.compile(f'(\\w+)({pairs_regex})')
        match = symbol_regex.match(symbol)
        if match:
            symbol = f'{match[1]}/{match[2]}'
        else:
            return False
    exchange.cancel_order(order['id'], symbol)
    return True


def cancel_orders(ticker, side='both'):
    """Cancels open orders for the ticker.

    Args:
        ticker: The ticker to cancel orders for.
        side: The side to cancel orders on. Can either be 'sell',
            'buy', or 'both'. Defaults to both.
    """
    orders = get_open_orders(ticker)
    if side == 'both':
        cancels = []
        cancels.extend(orders['sell'])
        cancels.extend(orders['buy'])
    else:
        cancels = orders[side]
    for order in cancels:
        cancel(order)


def cancel_all_orders(*tickers, side='both'):
    """Cancels open orders for all the tickers passed in.

    Args:
        *tickers: The tickers to cancel orders for. Defaults to
            nonzero balances if no tickers are supplied.
            (because only nonzero total balances can have open orders)
        side: The side to cancel orders for. Can either be 'sell',
            'buy', or 'both'. Defaults to both.
    """
    tickers = tickers if len(tickers) > 0 else get_nonzero_balances()
    for ticker in tickers:
        cancel_orders(ticker, side)


def get_usd_balance(ticker):
    """Returns the balance of a ticker in USD."""
    if ticker in ('USDT', 'USD'):
        return 1
    balance = get_balance(ticker, 'total')
    pairs = set(symbol.split('/')[1] for symbol in exchange.symbols)
    for pair in pairs:
        symbol = f'{ticker}/{pair}'
        if symbol in exchange.symbols:
            if f'{pair}/USDT' in exchange.symbols:
                pair_usd = get_symbol(f'{pair}/USDT')['bid']
                return pair_usd * balance * get_symbol(symbol)['bid']


def get_portfolio():
    """Returns the total value of funds in all accounts in USD."""
    balances = get_nonzero_balances()
    usd_balances = {ticker: get_usd_balance(ticker) for ticker in balances}
    total = sum(usd_balances.values())
    portfolio = {'total': total}
    for ticker in usd_balances:
        portfolio[ticker] = {}
        portfolio[ticker]['total'] = round(usd_balances[ticker], 2)
        portfolio[ticker]['percent'] = round(usd_balances[ticker]/total*100, 2)
    return portfolio
