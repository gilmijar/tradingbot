#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# import sth


class Base(object):
    def __init__(self, database):
        self.db = database
        self.last_trade = 0
        self.trades = None


class Stats(Base):
    def __init__(self, database):
        super().__init__(database)

    def getvwma(self, lookback):
        """get volume-weighted moving average"""
        querystring = """
        SELECT Sum(price * amount) / Sum(amount) vwma
        FROM trade
        WHERE tradeTimeStamp > %s;
        """
        vwma = self.db.generic_select(querystring, (lookback,))
        return vwma

    def getwma(self, lookback):
        """get 'freshness'-weighted moving average"""
        querystring = """
        SELECT Sum(price * (tradeTimeStamp - base)) / Sum(tradeTimeStamp - base) wma
        FROM trade
        INNER JOIN
        ( SELECT min(tradeTimeStamp)-1 base FROM trade WHERE tradeTimeStamp > %s) t2
        WHERE tradeTimeStamp > %s;
        """
        wma = self.db.generic_select(querystring, (lookback, lookback))
        return wma

    def getma(self, lookback):
        querystring = """
        SELECT Avg(price) ma
        FROM trade
        WHERE tradeTimeStamp > %s;
        """
        ma = self.db.generic_select(querystring, (lookback,))
        return ma

    def getstddev(self, lookback):
        querystring = """
        SELECT STDDEV(price) stddevpct
        FROM trade
        WHERE tradeTimeStamp > %s;
        """
        stddev = self.db.generic_select(querystring, (lookback,))
        return stddev

    def getamplitude(self, lookback):
        querystring = """
        SELECT Max(price) - Min(price) amp
        FROM trade
        WHERE tradeTimeStamp > %s;
        """
        amplitude = self.db.generic_select(querystring, (lookback,))
        return amplitude

    def getpricerangeatvolume(self, lookback, volume=0.9):
        querystring = """
        select
        min(p) minp
        , max(p) maxp
        from(
        select
        price p
        , (select
            sum(amount)
            FROM trade
            WHERE tradeTimeStamp > %(lookback)s
            AND price <= p ) / (select
            sum(amount)
            FROM trade
            WHERE tradeTimeStamp > %(lookback)s ) cvp
        from trade WHERE tradeTimeStamp > %(lookback)s
        group by
        price
        having cvp > %(volumelo)s and cvp < %(volumehi)s
        order by price asc
        ) hist
        """
        volumelo = round((1 - volume) / 2, 2)
        volumehi = 1 - volumelo
        amplitude = self.db.generic_select(
            querystring,
            {"lookback": lookback, "volumelo": volumelo, "volumehi": volumehi},
        )
        return amplitude


class Hourly(Base):
    def __init__(self, database):
        super().__init__(database)

    def get_candle(self, skip_hours=0):
        """fetches open, high, low,
        close, volume and number of trades in the last hourly candle"""
        querystring = """
            SELECT unix_timestamp(timeMark) tm, open, high, low, close, volume, tradeCount
            FROM candle1h
            WHERE timeMark = from_unixtime((unix_timestamp() DIV 3600 - 1 - %s) * 3600)
            """
        ohlcvn = self.db.generic_select(querystring, (skip_hours,))
        return ohlcvn

    def get_std_dev_hours(self, lookback_hours, skip_hours=0):
        querystring = """
        SELECT STDDEV(close)/AVG(close)*100 stddevpct
        FROM candle1h
        WHERE timeMark >= from_unixtime((unix_timestamp() DIV 3600 - %s) * 3600)  
        AND  timeMark < 
        from_unixtime((unix_timestamp() DIV 3600 - %s) * 3600)
        """
        std_dev_pct = self.db.generic_select(
            querystring, (lookback_hours + skip_hours, skip_hours)
        )
        return std_dev_pct

    def get_ma_hours(self, lookback_hours, skip_hours=0):
        querystring = """
        SELECT Avg(close) mah
        FROM candle1h
        WHERE timeMark >= from_unixtime((unix_timestamp() DIV 3600 - %s) * 3600)  
        AND  timeMark < from_unixtime((unix_timestamp() DIV 3600 - %s) * 3600)
        """
        mah = self.db.generic_select(
            querystring, (lookback_hours + skip_hours, skip_hours)
        )
        return mah

    def get_ma_volume_hours(self, lookback_hours, skip_hours=0):
        querystring = """
        SELECT Avg(volume) mavh
        FROM candle1h
        WHERE timeMark >= from_unixtime((unix_timestamp() DIV 3600 - %s) * 3600)  
        AND  timeMark < from_unixtime((unix_timestamp() DIV 3600 - %s) * 3600)
        """
        mavh = self.db.generic_select(
            querystring, (lookback_hours + skip_hours, skip_hours)
        )
        return mavh


class OrderMatcher(Base):
    def __init__(self, database):
        super().__init__(database)
        self.pre_matched_data = None
        pass

    def get_pre_matched_data(self):
        querystring = """
        SELECT * FROM placedTrade pt
        JOIN transactionTypeLookup ttl
        ON pt.tradeType = ttl.tradeType
        JOIN placedOrder po
        ON  po.orderType = ttl.orderType
        AND pt.tradeTimeStamp >= po.orderTimeStamp
        AND pt.price = po.price
        AND pt.baseAmount <= po.amount
        WHERE pt.orderId IS NULL
        ORDER BY po.ID
        """
        data = self.db.generic_select(querystring)
        return data

    def assign_orders_to_trades_simple(self):
        querystring = """
        UPDATE placedTrade pt 
        JOIN transactionTypeLookup ttl
        ON pt.tradeType = ttl.tradeType
        JOIN placedOrder po
        ON  po.orderType = ttl.orderType
        AND pt.tradeTimeStamp >= po.orderTimeStamp
        AND pt.price = po.price
        AND pt.baseAmount = po.amount
        SET pt.orderId = po.ID
        """
        data = self.db.generic_insert(querystring)
        return self.db.cursor.rowcount

    def assign_orders_to_trades_multiple(self):
        pre_matched_data = self.get_pre_matched_data()
        assigned_ids = {}
        trade_ids = []
        base_amount_sum = 0.0
        last_order_id = 0
        for row in pre_matched_data:
            if row[11] == last_order_id:
                base_amount_sum += row[5]
            else:
                assigned_ids = {}
                trade_ids = []
                base_amount_sum = 0.0
            last_order_id = row[11]
