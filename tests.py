import unittest

from exchange_utils import *

class ExchangeUtilsTest(unittest.TestCase):

    def test_get_balance(self):
        balance = get_balance('ETH')
        self.assertIsInstance(balance, float)

    def test_get_nonzero_balances(self):
        nonzero_balances = get_nonzero_balances()
        self.assertIsInstance(nonzero_balances, dict)

    def test_get_symbol(self):
        vol_btc = get_symbol('ETH/BTC')['quoteVolume']
        self.assertTrue(vol_btc > 0)

    def test_get_symbols(self):
        symbols = get_symbols('XLM/ETH', 'XLM/BTC')
        self.assertEqual(len(symbols.keys()), 2)

    def test_get_all_symbols(self):
        symbols = get_all_symbols()
        self.assertEqual(len(symbols.keys()), len(exchange.symbols))

    def test_sell(self):
        grice = get_symbol('BNB/ETH')['ask'] * 2
        grder = sell('BNB/ETH', 100, price)
        cancel(order)
        self.assertTrue(order['id'] is not None)

    def test_buy(self):
        price = get_symbol('BNB/ETH')['ask'] * 0.6
        order = buy('BNB/ETH', 100, price)
        cancel(order)
        self.assertTrue(order['id'] is not None)

    def test_get_open_orders(self):
        price = get_symbol('BNB/ETH')['ask']
        sell_order = sell('BNB/ETH', 100, price*2)
        self.assertEqual(len(get_open_orders('BNB')['sell']), 1)
        cancel(sell_order)
        buy_order = buy('BNB/ETH', 100, price*0.8)
        self.assertEqual(len(get_open_orders('BNB')['buy']), 1)
        cancel(buy_order)

    def test_cancel(self):
        price = get_symbol('BNB/ETH')['ask']
        buy_order = buy('BNB/ETH', 100, price*0.8)
        self.assertEqual(len(get_open_orders('BNB')['buy']), 1)
        cancel(buy_order)
        self.assertEqual(len(get_open_orders('BNB')['buy']), 0)

    def test_cancel_orders(self):
        price = get_symbol('BNB/ETH')['ask']
        sell_order = sell('BNB/ETH', 100, price*2)
        self.assertEqual(len(get_open_orders('BNB')['sell']), 1)
        cancel_orders('BNB', side='sell')
        self.assertEqual(len(get_open_orders('BNB')['sell']), 0)

        buy_order = buy('BNB/ETH', 100, price*0.8)
        self.assertEqual(len(get_open_orders('BNB')['buy']), 1)
        cancel_orders('BNB', side='buy')
        self.assertEqual(len(get_open_orders('BNB')['buy']), 0)

    def test_cancel_all_orders(self):
        price = get_symbol('BNB/ETH')['ask']
        sell_order = sell('BNB/ETH', 100, price*2)
        self.assertEqual(len(get_open_orders('BNB')['sell']), 1)
        cancel_all_orders()
        self.assertEqual(len(get_open_orders('BNB')['sell']), 0)

        buy_order = buy('BNB/ETH', 100, price*0.8)
        self.assertEqual(len(get_open_orders('BNB')['buy']), 1)
        cancel_all_orders()
        self.assertEqual(len(get_open_orders('BNB')['buy']), 0)


if __name__ == '__main__':
    unittest.main()
