#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import mysql.connector as mariadb


def query_proto(table_name, time_span_seconds):
    """return the query code. It is written to be driven by 2 variables for candle tables with various periodicity"""
    return """REPLACE INTO {0}
        (`ticker`, `timeMark`, `open`, `high`, `low`, `close`, `volume`, `tradeCount`, `sellVolume`, `sellCount`,
         `buyVolume`, `buyCount`, `openTime`, `closeTime`,`candleTime`) 
        SELECT 
            "BTCEUR" ticker, from_unixtime(t0.tbucket * {1}) t, t1.price O, high H, low L, t2.price C,
             volume V, tradeCount N, sellVolume sV, sellCount sC, buyVolume bV, buyCount bC, ot, ct, now() candleTime   

            FROM (
            SELECT
                min(tradeId) firstTrade,
                max(tradeId) lastTrade,
                from_unixtime(min(tradeTimeStamp)) ot,
                from_unixtime(max(tradeTimeStamp)) ct,
                max(price) high,
                min(price) low,
                sum(amount) volume,
                count(*) tradeCount,
                tradeTimeStamp DIV {1} tbucket
            FROM trade
            WHERE tradeTimeStamp > ifnull(( SELECT unix_timestamp(max(c.timeMark)) FROM {0} c ), 0)
            GROUP BY tbucket ORDER BY tbucket ASC
        ) t0 INNER JOIN trade t1 ON t1.tradeId = t0.firstTrade
        INNER JOIN trade t2 on t2.tradeId = t0.lastTrade
        INNER JOIN ( 
            SELECT 
            sum(amount) sellVolume
            , count(*) sellCount
            , tradeTimeStamp DIV {1} tbucket
            FROM trade
            WHERE tradeTimeStamp > ifnull(( SELECT unix_timestamp(max(c.timeMark)) FROM {0} c ), 0)           
            AND tradeType = 0
            GROUP BY tbucket ORDER BY tbucket ASC)  t_ask
        ON t0.tbucket = t_ask.tbucket
        INNER JOIN ( 
            SELECT 
            sum(amount) buyVolume
            , count(*) buyCount
            , tradeTimeStamp DIV {1} tbucket
            FROM trade
            WHERE tradeTimeStamp > ifnull(( SELECT unix_timestamp(max(c.timeMark)) FROM {0} c ), 0)
            AND tradeType = 1
            GROUP BY tbucket ORDER BY tbucket ASC)  t_bid
        ON t0.tbucket = t_bid.tbucket
        ORDER BY
        t
        """.format(table_name, time_span_seconds)


def candle5m(db):
    """
    add a set of data elemnts that allow amibroker
    to draw one 5-minute candle + volume with buy vs sell info
    """
    query_string = query_proto('candle5m', '300')
    db.execute(query_string)
    #    print(db.fetchwarnings())
    return db.rowcount


def candle1h(db):
    """
    add a set of data elemnts that allow amibroker
    to draw one 1-hour candle + volume with buy vs sell info
    """
    query_string = query_proto('candle1h', '3600')
    db.execute(query_string)
    #    print(db.fetchwarnings())
    return db.rowcount


def run_queries(user, password, database, host='localhost'):
    con = mariadb.connect(user=user, password=password, database=database, host=host)
    mydb = con.cursor()
    new_candles = candle5m(mydb)
    print("{} records added to candle5m table in {}".format(new_candles, database))
    new_candles = candle1h(mydb)
    print("{} records added to candle1h table in {}".format(new_candles, database))
    mydb.close()

#############
#   BEGIN   #
#############

bases = ('gdax', 'kraken')
for base in bases:
    run_queries('user', 'pass', base)

