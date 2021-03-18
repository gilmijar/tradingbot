#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import unittest
import api, db
from config import *
from functions import *


class TestFunctions(unittest.TestCase):
    def setUp(self):
        self.databases = ()
        self.databases += db.Gdax(DB_USER, DB_PASSWORD, dbhost='localhost', dbname='test_gdax'),
        self.databases += db.Kraken(DB_USER, DB_PASSWORD, dbhost='localhost', dbname='test_kraken'),

        self.public_apis = ()
        self.public_apis += api.GdaxPublic(),
        self.public_apis += api.KrakenPublic(),

        self.calling_frequencies = (2, 8, 5)
        # self.helper_clear_tables()

    def tearDown(self):
        pass

    def helper_clear_tables(self):
        truncate_trade = "TRUNCATE TABLE `trade`"
        for db in self.databases:
            db.generic_insert(truncate_trade)

    def fetch_row_counts(self):
        count_query = "SELECT Count(*) FROM `trade`"
        counts = ()
        for db in self.databases:
            counts += (db.generic_select(count_query)[0][0],)
        return counts

    def test_catchup_multi(self):
        # self.assertEqual(self.fetch_row_counts(), (0, 0, 0), 'tables not clean before testing')
        results = catchup_multi(
            self.public_apis, self.databases, self.calling_frequencies
        )
        self.assertGreater(results, 100)
        self.assertGreater(self.fetch_row_counts()[0], 100)
        self.assertGreater(self.fetch_row_counts()[1], 100)
        self.assertGreater(self.fetch_row_counts()[2], 100)

    def test_catchup_placed_trades(self):
        t_db = db.Gdax(DB_USER, DB_PASSWORD, dbhost=DB_HOST, dbname='test_gdax')
        t_api = api.GdaxPrivate(GDAX_KEYS['public'], GDAX_KEYS['private'])
        test_structure = (
            ("tradeId", "id"),
            ("baseCurrency", "currencyCrypto"),
            ("quoteCurrency", "currencyFiat"),
            ("baseAmount", "amountCrypto"),
            ("price", "rate"),
            ("tradeType", "type"),
            ("tradeTimeStamp", "time"),
        )
        t_db.generic_insert("TRUNCATE TABLE `placedTrade`")
        catchup_placed_trades(t_db, t_api, test_structure)
        rows_after = t_db.count_placed_trades()[0][0]
        t_api.close()
        t_db.close()
        self.assertGreater(rows_after, 0)
