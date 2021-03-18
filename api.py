#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import pycurl
import hmac
import hashlib
from base64 import b64decode, b64encode
import json
import time
from calendar import timegm
import data


class ApiBaseClass(object):
    @staticmethod
    def process_data(json_string):
        file_head = json_string[0:1]
        json_start = ("{", "[")
        json_end = ("}", "]")
        # check if one of the first characters is the expected character,
        # a sign that the file is json, not an "ERROR" html
        if json_start[0] in file_head:
            json_type = 0
        elif json_start[1] in file_head:
            json_type = 1
        else:
            raise NotJSON("response not in json format", json_string)
            # return {'success': False, 'reason': 'response not in json format'}
        # rpartition fixes "extra content error" when some extra bytes are saved at the end of the json file
        input_partitions = json_string.rpartition(json_end[json_type])
        # protect from unfinished files - no closing brace
        if 0 == len(input_partitions[0]):
            raise BrokenJSON("json string not closed", json_string)
            # return {'success': False, 'reason': 'json string not closed'}
        # if all was well - return the json object
        return json.loads(input_partitions[0] + json_end[json_type])

    @staticmethod
    def hash_message(msg, key):
        hashed_message = hmac.new(key, msg, hashlib.sha512)
        encoded_hash = hashed_message.hexdigest()
        return encoded_hash

    def __init__(self, baseurl=""):
        if "/" == baseurl[-1]:
            self.base_url = baseurl
        else:
            self.base_url = baseurl + "/"
        self.request_time = None
        self.response_time = None
        self.turnaround_time = None
        self.last_header = ""
        self.last_response = ""
        self.call_time_shift = 0
        self.api_default_encoding = "iso-8859-1"
        self.connection_timeout = 10
        self.user_agent = 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/534.30 (KHTML, like Gecko) \
            Ubuntu/11.04 Chromium/12.0.742.112 Chrome/12.0.742.112 Safari/534.30'
        self.connection = self.new_connection()
        self.proxy = None
        self.proxy_port = 0

    def new_connection(self):
        curlobj = pycurl.Curl()
        curlobj.setopt(curlobj.SSL_VERIFYPEER, 0)
        curlobj.setopt(curlobj.WRITEFUNCTION, self.content_writer)
        curlobj.setopt(curlobj.TIMEOUT, self.connection_timeout)
        curlobj.setopt(curlobj.NOPROGRESS, 1)
        # curlobj.setopt(curlobj.COOKIEFILE, filename)
        # or
        curlobj.setopt(curlobj.COOKIEJAR, "cookies")
        # curlobj.setopt(curlobj.DNS_CACHE_TIMEOUT, 10)
        curlobj.setopt(curlobj.HEADERFUNCTION, self.header_writer)
        # curlobj.setopt(curlobj.MAX_WRITE_SIZE, 65536) # that is 64 kibibytes, default is 16 KiB
        # curlobj.setopt(curlobj.MAX_HTTP_HEADER, 204800) # that is 200 kibibytes, default is 100 KiB
        # two opts above don't seem to work
        curlobj.setopt(curlobj.USERAGENT, self.user_agent)
        curlobj.setopt(curlobj.TCP_NODELAY, 1)
        curlobj.setopt(curlobj.URL, self.base_url)
        return curlobj

    def set_connection_option(self, option_object, option_value):
        self.connection.setopt(option_object, option_value)
        return True

    def reset_connection(self):
        self.close()
        self.connection = self.new_connection()

    def add_proxy(self, proxy, proxy_port=0):
        """add a proxy to the CURL connection
        call removeproxy to revert"""
        self.connection.setopt(self.connection.PROXY, proxy)
        self.proxy = proxy
        if proxy_port != 0:
            self.connection.setopt(self.connection.PROXYPORT, proxy_port)
            self.proxy_port = proxy_port

    def remove_proxy(self):
        """removes CURL proxy settings"""
        self.add_proxy("", 0)
        self.proxy = None
        self.proxy_port = 0

    def set_timeout(self, timeout):
        """
        set a timeout for curl connection

        :param timeout: timeout length in seconds
        :type timeout: int
        """
        self.connection_timeout = timeout
        self.connection.setopt(self.connection.TIMEOUT, self.connection_timeout)

    def close(self):
        self.connection.close()

    def content_writer(self, cont):
        self.last_response += cont.decode(self.api_default_encoding)
        return len(cont)

    def header_writer(self, cont):
        self.last_header += cont.decode(self.api_default_encoding)
        return len(cont)

    def last_response_code(self):
        response_code = self.last_header.splitlines()[0].split(" ")[1]
        return response_code

    def call_perform(self, address, data_handler):
        """Takes care of internet mechanics of the call
        rather than specifics of the website and URI
        :param address: string
        :param data_handler: class for an object
        """
        self.connection.setopt(self.connection.URL, address)
        # clear variables before appending new call's response
        self.last_response = ""
        self.last_header = ""
        self.request_time = time.time()
        self.connection.perform()  # do the Call
        self.response_time = time.time()
        self.turnaround_time = self.response_time - self.request_time
        if self.last_response_code() != "200":
            raise HTTPError(
                "HTTP error {}".format(self.last_response_code()), self.last_response
            )
        # initialize data object
        received_data = data_handler(self.process_data(self.last_response))
        # add headers to object
        received_data.response_headers = self.last_header
        # add plaintext response to object
        received_data.response_body = self.last_response
        # add call times to object
        received_data.request_send_time = self.request_time
        received_data.request_receive_time = self.response_time
        received_data.request_turnaround = self.turnaround_time
        return received_data

    @staticmethod
    def find_http_errors(header, body=""):
        first_line = header.splitlines()[0]
        protocol, first_line = first_line.partition(" ")[::2]
        response_code, response_text = first_line.partition(" ")[::2]
        if response_code != "200":
            raise HTTPError('{} {};\n {}'.format(response_code, response_text, body))


class GdaxPublic(ApiBaseClass):
    """
    Public API class.
    Has all the necessary things to communicate with the public
    API of api.gdax.com
    """

    def __init__(
        self, base_url="https://api.pro.coinbase.com/products/"
    ):  # https://api.gdax.com/products/BTC-EUR/book?level=2
        super().__init__(base_url)
        self.api_data_types = {"trade": "trades", "orderbook": "book"}
        self.currency_pair = "BTC-EUR"
        self.url = self.base_url + self.currency_pair + "/"
        self.connection = self.new_connection()

    def call(self, data_type, **param_dict):
        """send a GET HTTP request"""
        url_path = self.api_data_types[data_type]

        if param_dict is not None:
            get_request = "?" + "&".join(
                ["=".join(l2) for l2 in (zip(param_dict.keys(), param_dict.values()))]
            )
        else:
            get_request = ""
        if data_type == "trade":
            handler = data.GdaxTrades
        else:
            handler = data.GdaxOrders
        return self.call_perform(self.url + url_path + get_request, handler)

    def get_public_trades(self, since_trade=None):
        """pull public trades
        GDAX API's before and after params are trade ids
        non- intuitively, before=N will result in
        fetching trades that chronologically
        occured AFTER the Nth trade"""
        if since_trade is not None:
            resp = self.call("trade", before=since_trade)
        else:
            resp = self.call("trade")
        return resp

    def get_order_book(self, deatil_level=2):
        """pull public trades
        level (l) 2 is preferred.
        l=1 gets you just the two innermost orders, while 3
        gets the whole detailed response with ids"""

        resp = self.call("orderbook", level=str(deatil_level))
        return resp

    def get_public_history(self, since_trade=None):
        if since_trade is None:
            since_trade = 101
        else:
            since_trade += 101
        resp_count = 1
        while resp_count > 0:
            resp = self.call("trade", after=str(since_trade))
            resp_count = len(resp.raw)
            if resp.last < since_trade - 1:
                yield resp
                raise StopIteration
            since_trade = resp.last + 101
            yield resp


class KrakenPublic(ApiBaseClass):
    def __init__(self):
        base_url = "https://api.kraken.com/0/public/"
        super().__init__(base_url)
        self.api_data_types = {"trade": "Trades", "orderbook": "Depth", "time": "Time"}
        self.currency_pair = "XBTEUR"
        self.url = self.base_url
        self.connection = self.new_connection()

    def call(self, data_type, **param_dict):
        """send a GET HTTP request"""
        url_path = self.api_data_types[data_type]

        if param_dict is not None:
            get_request = "?" + "&".join(
                ["=".join(l2) for l2 in (zip(param_dict.keys(), param_dict.values()))]
            )
        else:
            get_request = ""
        if data_type == "trade":
            handler = data.KrakenTrades
        elif data_type == "orderbook":
            handler = data.KrakenOrders
        else:
            handler = data.ServerTime
        return self.call_perform(self.url + url_path + get_request, handler)

    def get_server_time(self):
        r = self.call("time")
        return r.raw

    def get_public_trades(self, since_trade=None):
        if since_trade is None:
            resp = self.call("trade", pair=self.currency_pair)
        else:
            resp = self.call("trade", pair=self.currency_pair, since=str(since_trade))
        return resp

    def get_order_book(self):
        resp = self.call("orderbook", pair=self.currency_pair)
        return resp

    def get_public_history(self, since_trade=None):
        if since_trade is None:
            since_trade = 0
        resp_count = 1
        while resp_count > 0:
            try:
                resp = self.call(
                    "trade", pair=self.currency_pair, since=str(since_trade)
                )
                resp_count = len(resp.raw)
                if 0 == resp_count:
                    return
                since_trade = resp.last
                yield resp
            except data.ServerError:
                time.sleep(10)
                print("Kraken be calmed. Set sail again!")


class GdaxPrivate(ApiBaseClass):

    def __init__(self, privatekey, publickey, password, baseurl='https://api.pro.coinbase.com'):
        super().__init__(baseurl)
        self.call_time_shift = 5
        self.private_key = b64decode(privatekey)
        self.public_key = publickey
        self.password = password
        self.url = self.base_url
        self.connection = self.new_connection()

    def call(self, method="POST", requestpath="", paramdict=None):
        message_timestamp = str(time.time() + self.call_time_shift)
        message = ""
        if "GET" == method:
            self.connection.setopt(self.connection.CUSTOMREQUEST, None)
            self.connection.setopt(self.connection.POST, 0)
            self.connection.setopt(self.connection.POSTFIELDS, "")
            self.connection.setopt(self.connection.HTTPGET, 1)
        elif "POST" == method:
            message = json.dumps(paramdict)
            self.connection.setopt(self.connection.CUSTOMREQUEST, None)
            self.connection.setopt(self.connection.POST, 1)
            self.connection.setopt(self.connection.POSTFIELDS, message)
        elif "DELETE" == method:
            self.connection.setopt(self.connection.CUSTOMREQUEST, "DELETE")
            self.connection.setopt(self.connection.POSTFIELDS, message)
        # postmessage = messagetimestamp + method + '/' + requestpath  + '/' + message
        postmessage = "{t}{mtd}/{rp}/{msg}".format(
            t=message_timestamp, mtd=method, rp=requestpath, msg=message
        )
        # add new HEADER params
        message_hash = self.hash_message(postmessage.encode("ascii"), self.private_key)
        self.connection.setopt(
            self.connection.HTTPHEADER,
            [
                "Content-Type: Application/JSON",
                "CB-ACCESS-SIGN: {}".format(message_hash),
                "CB-ACCESS-TIMESTAMP: {}".format(message_timestamp),
                "CB-ACCESS-KEY: {}".format(self.public_key),
                "CB-ACCESS-PASSPHRASE: {}".format(self.password),
            ],
        )
        new_url = self.url + requestpath + "/"
        self.connection.setopt(self.connection.URL, new_url)
        # clear variables before appending new call's response
        self.last_response = ""
        self.last_header = ""
        self.connection.perform()
        self.find_http_errors(self.last_header, self.last_response)
        return self.process_data(self.last_response)

    def get_accounts(self):
        request_method = "GET"
        request_path = "accounts"
        resp = self.call(request_method, request_path)
        return resp

    def get_balances(self, accounts_list=None, item_type="available"):
        """Get all balances and return available funds as dict
        if accounts are provided as a list, a call to api isn't made
        change item_type to get full balances rather than available funds

        :return: balances for different pairs
        :rtype: dict
        """
        if accounts_list is None:
            accountinfo = self.get_accounts()
        else:
            accountinfo = accounts_list
        balances = {}
        for infoitem in accountinfo:
            balances[infoitem["currency"]] = float(infoitem[item_type])
        return balances

    def place_trade(self, buysell, amount, rate, pair="BTC-EUR", notaker="true"):
        requestmethod = "POST"
        requestpath = "orders"
        params = {
            "product_id": pair,
            "side": buysell,
            "size": amount,
            "price": rate,
            "post_only": notaker,
        }
        # type - buy or sell; amount - how much crypto to buy or sell; rate - at what price
        resp = self.call(requestmethod, requestpath, params)
        return resp

    def cancel_all_orders(self, pair="BTC-EUR"):
        requestmethod = "DELETE"
        requestpath = "orders"
        params = {"product_id": pair}
        resp = self.call(requestmethod, requestpath, params)
        return resp


class KrakenPrivate(ApiBaseClass):
    # https://support.kraken.com/hc/en-us/articles/360029054811-What-is-the-authentication-algorithm-for-private-endpoints-
    @staticmethod
    def hash_message_kraken(uri_path, msg, key):
        digest = uri_path.encode() + hashlib.sha256(msg.encode()).digest()
        hashed_message = hmac.new(key, digest, hashlib.sha512)
        encoded_hash = b64encode(hashed_message.digest())
        return encoded_hash

    @staticmethod
    def nonce():
        """return a <=64bit integer
        used timegm from calendar module to reverse structured time
        given by gmtime() because in this way we can have universal time without DST
        an then added a scaled-up fractional part of monotonic clock, in part because
        timegm drops the fractional part, and in part because it has monotonic in the name

        :return: nonce for Kraken
        :rtype: int
        """
        return timegm(time.gmtime()) * 10 ** 8 + int(time.monotonic() * 10 ** 8)

    def __init__(
        self,
        privatekey,
        publickey,
        baseurl="https://api.kraken.com/",
        fixed_path="0/private/",
    ):
        super().__init__(baseurl)
        self.call_time_shift = 5
        self.private_key = b64decode(privatekey)
        self.public_key = publickey
        self.url = self.base_url
        self.fixed_path = fixed_path
        self.balances = {"total": {}, "reserved": {}}
        self.open_orders = []
        self.connection = self.new_connection()
        self.connection.setopt(self.connection.CUSTOMREQUEST, None)
        self.connection.setopt(
            self.connection.POST, 1
        )  # all Kraken private calls must be POST
        self.set_timeout(50)

    def call(self, requestpath="", paramdict=None):
        """convert paramdict to POST string and make the request to requestpath

        :param requestpath: URI path for the request
        :type requestpath: str
        :param paramdict: parameter names (as dict keys) and their values to be passed to server
        :type paramdict: dict
        """
        nonce = self.nonce()
        uripath = self.fixed_path + requestpath
        # prep and add the POST msg
        if paramdict is None:
            message = "nonce={}".format(nonce)
        else:
            message = "nonce={}&{}".format(
                nonce, "&".join(["{}={}".format(k, paramdict[k]) for k in paramdict])
            )
        self.connection.setopt(self.connection.POSTFIELDS, message)
        # add new HEADER params
        message_hash = self.hash_message_kraken(
            "/" + uripath, str(nonce) + message, self.private_key
        )
        self.connection.setopt(
            self.connection.HTTPHEADER,
            [
                "API-Key: {}".format(self.public_key),
                "API-Sign: {}".format(message_hash.decode('ascii')),
            ],
        )
        new_url = self.url + uripath
        self.connection.setopt(self.connection.URL, new_url)
        # clear variables before appending new call's response
        self.last_response = ""
        self.last_header = ""
        self.connection.perform()
        self.find_http_errors(self.last_header, self.last_response)
        return self.process_data(self.last_response)

    def get_accounts(self):
        request_path = "Balance"
        resp = self.call(request_path)
        if not resp["error"]:  # empty lists evaluate to False
            self.balances["total"] = {
                cur: float(resp["result"][cur]) for cur in resp["result"]
            }
        return resp

    def get_open_orders(self):
        request_path = "OpenOrders"
        resp = self.call(request_path)
        if resp["error"] == [] and 0 != len(resp["result"]):
            oo = resp["result"]["open"]
            self.open_orders = []
            self.balances["reserved"] = {}
            for order_id in oo:
                self.open_orders += [
                    {
                        "id": order_id,
                        "pair": oo[order_id]["descr"]["pair"],
                        "amount": float(oo[order_id]["vol"]),
                        "price": float(oo[order_id]["descr"]["price"]),
                        "type": oo[order_id]["descr"]["type"],
                        "creation": oo[order_id]["opentm"],
                    }
                ]
                if oo[order_id]["descr"]["type"] == "sell":
                    self.balances["reserved"][
                        oo[order_id]["descr"]["pair"][:4]
                    ] = self.balances["reserved"].get(
                        oo[order_id]["descr"]["pair"][:4], 0
                    ) + float(
                        oo[order_id]["vol"]
                    )
                else:
                    self.balances["reserved"][
                        oo[order_id]["descr"]["pair"][4:]
                    ] = self.balances["reserved"].get(
                        oo[order_id]["descr"]["pair"][4:], 0
                    ) + float(
                        oo[order_id]["vol"]
                    ) * float(
                        oo[order_id]["descr"]["price"]
                    )
        return resp

    def cancel_one_order(self, order_id):
        request_path = "CancelOrder"
        resp = self.call(request_path, {"txid": order_id})
        return resp

    def cancel_all_orders(self, pair=None):
        transaction_ids = ()
        open_orders = self.get_open_orders()
        if 0 == len(open_orders["result"]):
            return 0
        oo = open_orders["result"]["open"]
        for order in oo:
            if pair is None or oo[order]["descr"]["pair"] == pair:
                self.cancel_one_order(order)
                transaction_ids += (order,)
        return len(transaction_ids)

    def place_trade(
        self, buysell, amount, rate, pair="XXTZEUR", notaker="true", order_type="limit"
    ):
        request_path = "AddOrder"
        flags = ""
        if notaker == "true":
            flags += "post"
        params = {
            "pair": pair,
            "type": buysell,
            "ordertype": order_type,
            "volume": amount,
            "price": rate,
            "oflags": flags,
        }
        # type - buy or sell; amount - how much crypto to buy or sell; rate - at what price
        resp = self.call(request_path, params)
        return resp

    def get_operations(self, operation_type):
        request_path = "Ledgers"
        params = {"type": operation_type}
        resp = self.call(request_path, params)
        return resp


class Error(Exception):
    """Base class for exceptions in this module.
    when raising this provide server response as the argument
    """
    pass


class BadTimeStamp(Error):
    """To be raised when api responds with error error: 503, Invalid tonce value
    when raising this provide 3 args: error code as integer, error message as text and time as integer
    """
    # {error: 503, errorMsg: Invalid tonce value, time: 1480655376}
    pass


class NotJSON(Error):
    """Raised when response from server is not a JSON
    before raising try to check what the response is, like is it HTML?
    """
    pass


class BrokenJSON(Error):
    """Raised when response is JSON, but is incomplete, i.e. missing the closing brace
    When raising, provide length of string
    """


class NoSuccess(Error):
    """Generic exception for trade api success:false responses"""
    pass


# added on 6.11.2017
class HTTPError(Error):
    """Raised when HTTP response code is not 200
    this might make NotJSON error obsolete"""
    pass
