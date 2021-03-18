#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import unittest
import api
import db
from config import *


class KrakenTest(unittest.TestCase):
    def setUp(self):
        self.db = db.Kraken(DB_USER, DB_PASSWORD, dbhost=DB_HOST, dbname="test_kraken")
        self.public_api = api.KrakenPublic()
        self.helper_clear_tables()

    def tearDown(self):
        del self.public_api
        #self.helper_clear_tables()
        self.db.close()

    def helper_truncate(self, table_name):
        """truncate table_name"""
        self.db.generic_insert("TRUNCATE TABLE `{}".format(table_name))

    def helper_clear_tables(self):
        self.helper_truncate("trade")
        self.helper_truncate("orderbook")

    def test_insert_trades(self):
        select_query = "SELECT Count(*) FROM `trade`"
        trades = self.public_api.get_public_trades()
        self.db.put_trades(trades.as_tuples())
        self.assertEqual(len(trades.as_tuples()), self.db.generic_select(select_query)[0][0])

    def test_insert_orders(self):
        select_query = "SELECT Count(*) FROM `orderbook`"
        orderbook = self.public_api.get_order_book()
        self.db.put_orders(orderbook.as_tuples())
        self.assertEqual(len(orderbook.as_tuples()), self.db.generic_select(select_query)[0][0])
