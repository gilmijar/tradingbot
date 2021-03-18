#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import api
import unittest


class CloakingField:  # prevents base class from being run by unittest framework
    class TestBase(unittest.TestCase):
        def setUp(self):
            self.api_object = None
            self.since_value = None
            self.far_future = None
            self.sleep_time = 0.6

        def tearDown(self):
            del self.api_object

        def test_pull_public_trades(self):
            response_object = self.api_object.get_public_trades()
            self.assertIsInstance(response_object.raw, list)

        def test_pull_public_trades_historical(self):
            response_object = self.api_object.get_public_trades(5000)
            self.assertIsInstance(response_object.raw, list)

        def test_orderbook(self):
            response_object = self.api_object.get_order_book()
            self.assertIsInstance(response_object.raw, dict)
            self.assertIn("asks", response_object.raw.keys())
            self.assertIn("bids", response_object.raw.keys())

        def test_pull_history(self):
            total_count = 0
            for data_object in self.api_object.get_public_history(self.since_value):
                api.time.sleep(self.sleep_time)
                total_count += len(data_object.as_tuples())
            self.assertGreater(total_count, 100)

        def test_pull_history_empty(self):
            total_count = 0
            for data_object in self.api_object.get_public_history(self.far_future):
                api.time.sleep(self.sleep_time)
                total_count += len(data_object.as_tuples())
            self.assertEqual(total_count, 0)

        def test_proxy_use_with_test_orderbook(self):
            from config import PROXIES
            for host, detail in PROXIES.items():
                with self.subTest(host=host):
                    self.api_object.add_proxy(detail["ip"], detail["port"])
                    response_object = self.api_object.get_order_book()
                    self.assertIsInstance(response_object.raw, dict)
                    self.assertIn("asks", response_object.raw.keys())
                    self.assertIn("bids", response_object.raw.keys())
                    self.api_object.remove_proxy()


class TestKrakenApi(CloakingField.TestBase):
    def setUp(self):
        self.api_object = api.KrakenPublic()
        self.since_value = 1507328809129542315
        self.far_future = 9999999999999999999
        self.sleep_time = 6

    @unittest.skip("takes too long")
    def test_pull_history(self):
        pass

    def test_orderbook(self):
        pass

    def test_pull_public_trades(self):
        pass

    def test_pull_public_trades_historical(self):
        pass

    def test_pull_history_empty(self):
        pass

    def test_proxy_use_with_test_orderbook(self):
        pass


class TestGdaxApi(CloakingField.TestBase):
    def setUp(self):
        self.api_object = api.GdaxPublic()
        self.since_value = 16319800
        self.far_future = 99999999
        self.sleep_time = 0.6

    @unittest.skip("takes too long")
    def test_pull_history(self):
        pass

    @unittest.skip("does not apply to gdax")
    def test_pull_public_trades_historical(self):
        pass

    @unittest.skip("to be fixed at a later date")
    def test_pull_history_empty(self):
        pass

    def test_orderbook(self):
        pass

    def test_pull_public_trades(self):
        pass
