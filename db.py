#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import time
import mysql.connector as mariadb


class Db(object):
    @staticmethod
    def two_level_implode(structured):
        lev_one = (
            "('{}')".format("', '".join(map(str, inner_set)))
            for inner_set in structured
        )
        lev_two = ", ".join(lev_one)
        return lev_two

    def __init__(self, un, pw, dbname="test", dbhost="localhost", compress=False, **kwargs):
        self.connection = mariadb.connect(
            user=un, password=pw, database=dbname, host=dbhost, compress=compress, **kwargs
        )
        # https://dev.mysql.com/doc/connector-python/en/connector-python-api-mysqlconnection-cursor.html
        self.cursor = self.connection.cursor()
        # self.cursor = self.connection.cursor(named_tuple=True)

    def close(self):
        self.cursor.close()

    def start_transaction(self):
        """Do not use in Aria tables - as of 15.09.2017 Aria engine has no user controllable transactions yet"""
        self.connection.start_transaction()

    def commit(self):
        """Do not use in Aria tables - as of 15.09.2017 Aria engine has no user controllable transactions yet"""
        self.connection.commit()

    def rollback(self):
        """Do not use in Aria tables - as of 15.09.2017 Aria engine has no user controllable transactions yet"""
        self.connection.rollback()

    def generic_insert(self, querystring, value_list=None):
        if value_list is None:
            self.cursor.execute(querystring)
        elif isinstance(value_list[0], tuple):
            self.cursor.executemany(querystring, value_list)
        else:
            self.cursor.execute(querystring, value_list)
        return self.cursor.lastrowid

    def get_trade_count(self, time_span_minutes):
        querystring = "SELECT count(*) tradeCount FROM trade WHERE tradeTimeStamp > %s;"
        self.cursor.execute(querystring, (int(time.time()) - 60 * time_span_minutes,))
        return self.cursor.fetchone()

    def get_last_trade(self):
        querystring = "SELECT max(tradeId) FROM trade"
        self.cursor.execute(querystring)
        return self.cursor.fetchone()

    def get_orderbook(self, side, step):
        lookup = {"ask": -1, "bid": 1}
        querystring = "SELECT max(orderTimeStamp) FROM orderbook WHERE step = %s;"
        self.cursor.execute(querystring, (step * lookup[side],))
        last_timestamp = self.cursor.fetchone()[0]
        querystring = "SELECT * FROM orderbook WHERE orderTimeStamp = %s;"
        self.cursor.execute(querystring, (last_timestamp, step * lookup[side]))
        result = self.cursor.fetchall()
        """
        if 1 < len(result):
            sendMessage("two records received when one was expected: " + str(result))
        """
        return result[0]

    def put_balance(self, btc, pln, price=0):
        querystring = """
                SELECT balanceTimeStamp, btc, pln FROM balance
                WHERE balanceTimeStamp = (SELECT max(balanceTimeStamp) m FROM balance)
                """
        self.cursor.execute(querystring)
        last_one = self.cursor.fetchone()
        if btc != float(last_one[1]) or pln != float(last_one[2]):
            querystring = """
                    INSERT IGNORE INTO balance (balanceTimeStamp, btc, pln, price)
                    VALUES (%s, %s, %s, %s)
                    """
            ts = int(time.time())
            self.cursor.execute(querystring, (ts, btc, pln, price))
            return "logged balance to db"
        else:
            return "no change in balances"

    def get_balance(self, timespan):
        querystring = """
                SELECT balanceTimeStamp, btc, pln, price
                FROM balance WHERE balanceTimeStamp > %s
                ORDER BY balanceTimeStamp ASC
        """
        valuelist = (time.time() - timespan,)
        self.cursor.execute(querystring, valuelist)
        result = self.cursor.fetchall()
        return result

    def put_error(self, error, stamp):
        try:
            error_module = error.__module__
        except AttributeError:
            error_module = "None"
        error_class = error.__class__.__name__
        if isinstance(error.args[0], int):
            error_code = error.args[0]
            error_text = "; ".join([str(x) for x in error.args[1:]])
        else:
            error_code = None
            error_text = "; ".join([str(x) for x in error.args[0:]])
        querystring = (
            "INSERT IGNORE INTO errorlog (errorModule, errorClass, errorCode, errorText, errorTimeStamp) "
            "VALUES (%s, %s, %s, %s, %s)"
        )
        valuelist = (error_module, error_class, error_code, error_text, stamp)
        self.cursor.execute(querystring, valuelist)
        return self.cursor.lastrowid

    def put_trades(self, data_as_list_of_tuples, bulk=False):
        """insert trades into table
        need data as list of tuples
        with
        timestamp, amount, price, trade type (as number), trade id
        trade type is: ask=0 bid=1
        if bulk == TRUE then data is inserted into querystring as text
        this is a workaround for connector not optimizing bulk inserts"""
        querystring = """
            INSERT IGNORE INTO trade (
                tradeTimeStamp
                , amount
                , price
                , tradeType
                , tradeId)"""
        if bulk:
            querystring += """
                VALUES {}
            """.format(
                self.two_level_implode(data_as_list_of_tuples)
            )
            self.cursor.execute(querystring)
        else:
            querystring += """
            VALUES (%s, %s, %s, %s, %s)
            """
            self.cursor.executemany(querystring, data_as_list_of_tuples)
        return self.cursor.rowcount

    def put_orders(self, data_as_list_of_tuples, bulk=False):
        """Insert orders into tables
        data as list of tuples with
        price, amount, timeStamp, step (with negative values for ask type
        if bulk == TRUE then data is inserted into querystring as text
        this is a workaround for connector not optimizing bulk inserts"""
        querystring = """
            INSERT IGNORE INTO orderbook (price
                , amount
                , orderTimeStamp
                , step)"""
        if bulk:
            querystring += """
                VALUES {}
            """.format(
                self.two_level_implode(data_as_list_of_tuples)
            )
            self.cursor.execute(querystring)
        else:
            querystring += """
            VALUES (%s, %s, %s, %s)
            """
            self.cursor.executemany(querystring, data_as_list_of_tuples)
        return self.cursor.rowcount

    def put_turnaround(self, valuelist):
        """Log RTT in db"""
        querystring = """
        INSERT INTO `requestTime`
        (
        `requestType`,
        `sent`,
        `received`,
        `duration`)
        VALUES
        (%s, %s, %s, %s);
        """
        self.cursor.execute(querystring, valuelist)
        return self.cursor.lastrowid

    def generic_select(self, querystring, valuelist=None):
        """.. function:: genericselect(querystring[, valuelist])

        execute a select query and return all results

        a list (tuple) of parameters can be passed
           to be used with the parameters, if the query has them
        :param querystring: the query to execute
        :type querystring: string
        :param valuelist: a tuple of arguments to be passed as query params
        :type valuelist: tuple
        :rtype: list of tuples
        """
        if valuelist is None:
            self.cursor.execute(querystring)
        elif isinstance(valuelist, (tuple, dict)):
            self.cursor.execute(querystring, valuelist)
        result = self.cursor.fetchall()
        return result


class Kraken(Db):
    pass


class Gdax(Db):
    def put_orders(self, data_as_list_of_tuples, bulk=False):
        """Insert orders into tables
        data as list of tuples with
        price, amount, orderCount, timeStamp, step"""
        querystring = """
            INSERT IGNORE INTO orderbook (price
                , amount
                , orderCount
                , orderTimeStamp
                , step)
        """
        if bulk:
            querystring += """
                VALUES {}
            """.format(
                self.two_level_implode(data_as_list_of_tuples)
            )
            self.cursor.execute(querystring)
        else:
            querystring += """
            VALUES (%s, %s, %s, %s, %s)
            """
            self.cursor.executemany(querystring, data_as_list_of_tuples)
        return self.cursor.lastrowid
