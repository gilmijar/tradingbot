#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import unittest
import api


class GdaxTest(unittest.TestCase):
    def setUp(self):
        self.public_api = api.GdaxPublic()
        self.orderbook = self.public_api.get_order_book()
        self.trades = self.public_api.get_public_trades()

    def tearDown(self):
        del self.public_api
        del self.orderbook

    def test_finding_big_orders(self):
        whales = self.orderbook.get_whales()
        # print (whales)
        self.assertIsInstance(whales["asks"], float)
        self.assertGreater(whales["asks"], whales["bids"])

    def test_trades_as_tuples(self):
        data = self.trades.as_tuples()
        self.assertIsInstance(data, list)
        self.assertIsInstance(data[0], tuple)


class KrakenTest(GdaxTest):
    def setUp(self):
        self.public_api = api.KrakenPublic()
        self.orderbook = self.public_api.get_order_book()
        self.trades = self.public_api.get_public_trades()

    def test_trades_as_tuples(self):
        data = self.trades.as_tuples()
        self.assertIsInstance(data, list)
        self.assertIsInstance(data[0], tuple)
        self.assertEqual(data[-1][4], self.trades.last)
        self.assertLess(data[-2][4], self.trades.last)
        previous_tid = 0
        for trade in data:
            self.assertNotEqual(trade[4], previous_tid)
            previous_tid = trade[4]
            # print(previous_tid)
