#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import unittest
import db
import stats
from config import *


class GdaxTestBase(unittest.TestCase):
    def setUp(self):
        self.database = db.Gdax(
            DB_USER, DB_PASSWORD, dbhost=DB_HOST, dbname="test_bitmarket"
        )
        self.statistics_hourly = stats.Hourly(self.database)
        self.order_matcher = stats.OrderMatcher(self.database)

    def tearDown(self):
        del self.database
        del self.statistics_hourly

    def test_stddev_hours(self):
        stddev = self.statistics_hourly.get_std_dev_hours(72)[0][0]
        self.assertIsInstance(stddev, float)

    def test_stddev_prevous_hours(self):
        stddev = self.statistics_hourly.get_std_dev_hours(72, 72)[0][0]
        self.assertIsInstance(stddev, float)

    def test_ma_hours(self):
        ma = self.statistics_hourly.get_ma_hours(72)[0][0]
        self.assertGreaterEqual(ma, 0)

    def test_ma_volume_hours(self):
        ma = self.statistics_hourly.get_ma_volume_hours(72)[0][0]
        self.assertGreaterEqual(ma, 0)

    def test_last_candle_hours(self):
        candle = self.statistics_hourly.get_candle()[0]
        self.assertEqual(7, len(candle))

    def test_get_pre_matched_data(self):
        data = self.order_matcher.get_pre_matched_data()
        for row in data:
            print(row)
        self.assertIsNotNone(data[0])

    def test_assign_orders_to_trades_simple(self):
        # TODO: create new schema to store fresh test data
        data = self.order_matcher.assign_orders_to_trades_simple()
        print(data)
        self.order_matcher.db.commit()
        self.assertIsNotNone(data)
