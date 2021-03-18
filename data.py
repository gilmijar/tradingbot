#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import time
from calendar import timegm


class BaseDataClass(object):
    """Base class for market response and data
    Stores also some trace info, like headers, request URI, request times"""

    def _init_(self):
        self.raw = None
        self.request_type = None
        self.request_type_text = {0: "trade", 1: "orderbook"}
        self.request_send_time = None
        self.request_receive_time = None
        self.request_turnaround = None
        self.response_body = None
        self.response_headers = None

    def as_rtt(self):
        return (
            self.request_type,
            self.request_send_time,
            self.request_receive_time,
            self.request_turnaround,
        )


class BaseTrades(BaseDataClass):
    """
    Stores market trade data and provides
    handy methods for data transformation into
    other formats
    """

    def __init__(self, trades):
        super().__init__()
        if trades is None or len(trades) == 0:
            raise EmptyData(1, "No data supplied to Trades object")
        self.raw = trades
        self.trade_types = {"buy": 1, "sell": 0}
        self.request_type = 0

    def as_keys(self):
        """returns a tuple with data keys. Only keys of the first dict are returned"""
        return self.raw[0].keys()

    def as_tuples(self):
        """
        returns data as a list of tuples,
        Elements of each tuple are in fixed order as follows:
        time, amount, price, side, tradeId -
        :return: list of tuples
        """
        order = ("time", "size", "price", "side", "trade_id")
        out = []
        for r in self.raw:
            component = ()
            for item in order:
                if "side" == item:
                    component += (self.trade_types[r[item]],)
                elif "time" == item:
                    usable_time = r[item].rpartition(".")[0]
                    if usable_time == "":
                        usable_time = r[item].rpartition("Z")[0]
                    timetuple = time.strptime(usable_time, "%Y-%m-%dT%H:%M:%S")
                    component += (timegm(timetuple),)
                else:
                    component += (r[item],)
            out += [component]
        return out


class GdaxTrades(BaseTrades):
    def __init__(self, trades):
        super().__init__(trades)
        self.last = int(trades[0]["trade_id"])


class KrakenTrades(BaseTrades):
    def __init__(self, trades):
        self.pair = ""
        self.ticker = ""
        self.set_pair(("XBT", "EUR"))
        super().__init__(trades)
        try:
            self.raw = trades["result"][self.ticker]
        except:
            if "EService:Unavailable" in trades["error"]:
                print("Kraken be like angry, need to be quiet")
                raise ServerError("EService:Unavailable")
            else:
                print(trades)
                raise
        self.last = int(trades["result"]["last"])
        self.trade_types = {"b": 1, "s": 0}

    def set_pair(self, pair):
        self.pair = pair[0] + pair[1]
        self.ticker = "X{0}Z{1}".format(*pair)

    def as_tuples(self, *ignored_args):
        """
        returns data as a list of tuples,
        Elements of each tuple are in fixed order as follows:
        time, amount, price, side, tradeId -
        we calculate tid to at least be able to use it as a since parameter in REST requests
        :arg: ignored_Args - is here for compatibility
        :return: list of tuples
        """
        if 0 == len(self.raw):
            raise EmptyData(1, "No trades in list")
        data_elements = {"price": 0, "amount": 1, "time": 2, "side": 3}
        out = []
        id_suffix = 0
        previous_time_stamp = 0.00
        for trade in self.raw:
            component = ()
            component += (int(trade[data_elements["time"]]),)
            component += (trade[data_elements["amount"]],)
            component += (trade[data_elements["price"]],)
            component += (self.trade_types[trade[data_elements["side"]]],)
            if previous_time_stamp == trade[data_elements["time"]]:
                id_suffix = 0
            component += (int(trade[data_elements["time"]] * 10 ** 9 + id_suffix),)
            previous_time_stamp = trade[data_elements["time"]]
            id_suffix += 1
            out += [component]
        out[-1] = out[-1][:4] + (self.last,)  # this is bad, but what to do when they won't give us the IDs
        return out


class BaseOrders(BaseDataClass):
    """
    stores market orderbook and provides
    handy methods for data transformation
    """

    def __init__(self, orders, the_time=None):
        super().__init__()
        if orders is None or len(orders) == 0:
            raise EmptyData(2, "No data supplied to Orders object")
        if the_time is not None:
            self.order_time = int(the_time)
        else:
            self.order_time = int(time.time())
        self.raw = orders
        # self.sequence = orders['sequence']
        self.order_types = {"bids": 1, "asks": -1}
        self.request_type = 1
        self.order_element_count = 3  # how many useful elements are expected in one order: price, vol, anything else?

    def get_one(self, step, side):
        """
        Returns Nth order from one side of the orderbook
        :param step: int, which order
        :param side: str (bids|asks), which side
        :return: tuple, (price, volume, ordercount)
        """
        # sidenumeric = self.ordertypes[side]
        return tuple(self.raw[side][step])

    def get_whales(self, inner=20):
        """
        Returns a dictionary containing the largest bid and largest ask by volume
        in the inner 20 orders on each side
        :return: dict (ask_price, bid_price)
        """
        out = {}
        for order_type in self.order_types:
            max_volume = 0
            max_vol_price = 0
            for order in self.raw[order_type][:inner]:
                v = float(order[1])
                p = float(order[0])
                if v > max_volume:
                    max_volume = v
                    max_vol_price = p
            out[order_type] = max_vol_price
        return out

    def as_tuples(self, inner=None, side="both"):
        """
        Returns N lowest asks and/or N highest bids.
        Data is a list of tuples. tuple order is:
        type , price, amount, timestamp, step
        type has 1 for bids and 0 for asks
        :param inner: how many orders to display (ommit to get all data)
        :param side: [ask(s)|bid(s)|both(default)]
        :return: list of tuples
        """
        out = []
        order_types = tuple(self.order_types.keys())
        if side[:3] == order_types[0][:3]:
            sides = (order_types[0],)
        elif side[:3] == order_types[1][:3]:
            sides = (order_types[1],)
        else:
            sides = order_types
        for side in sides:
            step = 0
            for order in self.raw[side]:
                if inner == step:
                    break
                step += 1
                component = ()
                #component += (self.order_types[side],)
                component += tuple(order[: self.order_element_count])
                component += (self.order_time,)
                component += (step * self.order_types[side],)
                out += [component]
        return out


class GdaxOrders(BaseOrders):
    """take all from base class"""
    pass


class KrakenOrders(BaseOrders):
    def __init__(self, orders, the_time=None):
        super().__init__(orders, the_time)
        tmp = orders["result"]
        self.raw = tmp[list(tmp.keys())[0]]
        self.order_element_count = 2  # see base class for info


class ServerTime(BaseDataClass):
    """
    Simple class for compatibility with others
    when asking server for time.
    """

    def __init__(self, server_time):
        super().__init__()
        if server_time is None or len(server_time) == 0:
            raise EmptyData(3, "No data supplied to ServerTime object")
        self.raw = server_time
        self.requesttype = 2

    def as_timestamp(self):
        return int(self.raw["result"]["unixtime"])


class EmptyData(Exception):
    """Raised when data passed to object is empty
    code 1 is for empty trades
    code 2 - for empty orders
    code 3 - for empty server time"""
    pass


class ServerError(Exception):
    """This is meant to reflect some or all errors that come
    as communication from API, instead of data.
    Make sure to give a proper description when raising"""
    pass
