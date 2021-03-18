#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import api
from config import *
import unittest


class GdaxTestBase(unittest.TestCase):
    def setUp(self):
        self.private_api = api.GdaxPrivate(
            GDAX_KEYS["private"], GDAX_KEYS["public"], GDAX_KEYS["password"]
        )

    def tearDown(self):
        self.private_api.close()
        del self.private_api

    def test_pulling_account_info(self):
        accountinfo = self.private_api.get_accounts()
        self.assertIsInstance(accountinfo, list)
        self.assertIsInstance(accountinfo[0], dict)

    def test_pulling_balances(self):
        expectedcurrencies = ("EUR", "BTC")
        balances = self.private_api.get_balances()
        for currency in expectedcurrencies:
            self.assertIn(
                currency, balances.keys(), "missing balance for {}".format(currency)
            )
        for currency in expectedcurrencies:
            self.assertIsInstance(
                balances["EUR"], float, "balance in {} is not a float".format(currency)
            )

    def test_extracting_balances_with_acct_info_provided(self):
        account_info = self.private_api.get_accounts()
        expected_currencies = ("EUR", "BTC")
        # set proxy to a bogus ip, to make sure we don't make another call via api (or it will fail)
        self.private_api.add_proxy("127.0.0.2", 12345)
        balances = self.private_api.get_balances(account_info)
        self.private_api.remove_proxy()  # remove proxy
        for currency in expected_currencies:
            self.assertIn(
                currency, balances.keys(), "missing balance for {}".format(currency)
            )
        for currency in expected_currencies:
            self.assertIsInstance(
                balances["EUR"], float, "balance in {} is not a float".format(currency)
            )

    def test_pulling_total_balances(self):
        expected_currencies = ("EUR", "BTC")
        balances = self.private_api.get_balances(item_type="balance")
        for currency in expected_currencies:
            self.assertIn(
                currency, balances.keys(), "missing balance for {}".format(currency)
            )
        for currency in expected_currencies:
            self.assertIsInstance(
                balances["EUR"], float, "balance in {} is not a float".format(currency)
            )


class KrakenTest(unittest.TestCase):
    def setUp(self):
        self.private_api = api.KrakenPrivate(
            privatekey=KRAKEN_KEYS["private"], publickey=KRAKEN_KEYS["public"]
        )

    def tearDown(self):
        self.private_api.close()
        del self.private_api
        api.time.sleep(15)  # so that they don't block us when we test

    @unittest.skip("temporary skip")
    def test_nonce_generation(self):
        x = self.private_api.nonce()
        for i in range(1000000):
            y = self.private_api.nonce()
            self.assertGreater(
                y, x, "nonce on iteration {} not bigger than previous one".format(i)
            )
            x = y

    def test_pulling_account_info(self):
        account_info = self.private_api.get_accounts()
        self.assertEqual(account_info["error"], [])
        self.assertIsInstance(account_info["result"], dict)
        print(account_info["result"])

    # @unittest.skip('for separate test')
    def test_pulling_open_orders(self):
        open_orders = self.private_api.get_open_orders()
        self.assertEqual(open_orders["error"], [])
        self.assertIsInstance(open_orders["result"], dict)
        print(self.private_api.open_orders)

    @unittest.skip("for separate test")
    def test_placing_sell_order(self):
        # https://www.kraken.com/help/api#add-standard-order
        price = 8000 + int(api.time.time() * 10 % 100)
        new_order = self.private_api.place_trade(
            "sell", 0.004, price, "XXBTZEUR", "true"
        )
        self.assertEqual(new_order["error"], [])
        # api.time.sleep(7)
        open_orders = self.private_api.get_open_orders()
        order_ids = open_orders["result"]["open"].keys()
        self.assertIn(new_order["result"]["txid"][0], tuple(order_ids))
        # (self, buysell, amount, rate, pair = 'BTC-EUR', notaker = 'true'):

    @unittest.skip("for separate test")
    def test_cancelling_one_order(self):
        open_orders = self.private_api.get_open_orders()
        order_ids = open_orders["result"]["open"].keys()
        self.assertGreater(len(order_ids), 0, "No orders to cancel!")
        # api.time.sleep(7)
        cancellation_output = self.private_api.cancel_one_order(list(order_ids)[0])
        self.assertEqual(cancellation_output["error"], [])
        self.assertEqual(cancellation_output["result"]["count"], 1)

    @unittest.skip('for separate test')
    def test_cancelling_orders(self):
        open_orders = self.private_api.get_open_orders()
        order_ids = open_orders["result"]["open"].keys()
        self.assertGreater(len(order_ids), 0, "No orders to cancel!")
        # api.time.sleep(7)
        cancellation_output = self.private_api.cancel_all_orders()
        self.assertEqual(cancellation_output, len(order_ids))

    def test_placing_and_cancelling_orders(self):
        # https://www.kraken.com/help/api#add-standard-order
        # noinspection PyUnusedLocal
        for i in (1, 2, 3):
            price = 8000 + int(api.time.time() * 10 % 100)
            new_order = self.private_api.place_trade(
                "sell", 0.004, price, "XXBTZEUR", "true"
            )
            self.assertEqual(new_order["error"], [])
            api.time.sleep(2)
        open_orders = self.private_api.get_open_orders()
        order_ids = open_orders["result"]["open"].keys()
        self.assertGreater(len(order_ids), 0, "No orders to cancel!")
        cancellation_output = self.private_api.cancel_one_order(list(order_ids)[0])
        self.assertEqual(cancellation_output["error"], [])
        self.assertEqual(cancellation_output["result"]["count"], 1)
        api.time.sleep(2)
        cancellation_output = self.private_api.cancel_all_orders()
        self.assertEqual(cancellation_output, len(order_ids) - 1)

    def test_pulling_operations(self):
        oper = self.private_api.get_operations("deposit")
        self.assertEqual(oper["error"], [])
        # self.assertEqual(cancellation_output['result']['count'], 1)

