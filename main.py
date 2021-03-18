#!/usr/bin/env python3
# -*- coding: utf-8 -*-


# from functions import * #import objects here
import api
import db
import comm
import stats
from config import *
from functions import *
from traceback import format_tb as traceback_format


def wrap_up():
    cryptowatch_api.close()
    transaction_api.close()
    print("")
    print("-" * 15)
    print("closed Api connection")
    database.commit()
    database.close()
    print("closed db connection")
    print(time.ctime())
    print("<---- QUITTING ---->")


"""
start cryptowatch
- make an api object
- make a db object
- query api and insert into db in a loop
"""

stats_file_name = '/dev/shm/gdax.stats'
communicator = comm.Comm('Trade_bot_test_run', 'email@example.com')

#leaving as example
#database = db.Bitmarket(DB_USER, DB_PASSWORD, dbname='bitmarket', dbhost='aruba')
# database = db.Gdax(DBUSER, DBPASSWORD, dbname='gdax', dbhost='localhost')
#cryptowatch_api = api.BitmarketPublic()
#transaction_api = api.BitmarketPrivate(BITMARKET_KEYS['public'], BITMARKET_KEYS['private'])
#cryptowatch_api.add_proxy(PROXIES["sirius"]["ip"], PROXIES["sirius"]["port"])
#transaction_api.add_proxy(PROXIES["sirius"]["ip"], PROXIES["sirius"]["port"])

statistics = stats.Stats(database)
statistics_hourly = stats.Hourly(database)

print("bringing trade table up to speed...")
t0 = time.time()
public_apis = (cryptowatch_api,)
databases = (database,)
calling_frequencies = (0.61,)
results = catchup_multi(public_apis, databases, calling_frequencies, True)
t1 = time.time()
print("new trades pulled: ", results)
print("that took", int(t1 - t0), "seconds")
error_stats = {"otherErrors": 0, "noErrors": 0}


imperative_table = {1: (0, 1), 2: (1, 0), 3: (1, 1), 4: (0, 0)}
t0 = time.time()
cancellation_trigger = 0
# these might be overridden by setmyvars()
# imperative overrides algo signals
# use it when a sell or buy is needed no matter the market situation
# imperative values: 0 - auto; 1 - buy; 2- sell; 3 - both; 4 - none
# auto trades normally - no imperative
# buy and sell do only buying and selling respectively
# both = janusz
# none no trading at all, even if there are signals
imperative = 0

exec_buy = 0
exec_sell = 0
trading_timeout = 240

activity_indicator = ""
previous_strategy = current_strategy = "none"
newline_timeout = 240
next_newline_time = time.time()
orders_save_timeout = 30
next_orders_save_time = 0
bid_placement = 2  # zero-based
ask_placement = 2  # zero-based

while 100 > max_dict_val(error_stats):
    try:
        n = set_my_vars("settings.txt", globals())
        trades = catchup_multi(public_apis, databases, calling_frequencies)
        if trades[tuple(trades.keys())[0]] > 0:
            activity_indicator = "+"
        else:
            activity_indicator = "."

        # cancel orders if it's time
        if time.time() > cancellation_trigger:
            cancellation_trigger = time.time() + trading_timeout
            cancellation_response = transaction_api.cancel_all_orders()
            activity_indicator += "x"
            if len(cancellation_response["success"]) > 0:
                database.delete_placed_orders(cancellation_response["success"])
                # TODO: placed trade history pull here, and matching also here
        # end cancel orders

        try:
            orderbook = cryptowatch_api.get_order_book()
            database.put_turnaround(orderbook.as_rtt())
            # only save orders once every N seconds
            if next_orders_save_time < time.time():
                database.put_orders(orderbook.as_tuples(inner=300))
                next_orders_save_time = time.time() + orders_save_timeout
            # Now place some orders
            # get the balances
            available_funds = transaction_api.get_balances()
            current_strategy = "janusz"
            exec_sell, exec_buy = 1, 1
            # here we override algos to account for imperative settings
            if imperative in imperative_table:
                exec_sell, exec_buy = imperative_table[imperative]

            # calculate the bid and ask price
            # but if the calculated price makes us the taker, make the price so that we are makers
            bid_price = round(
                float(orderbook.get_one(bid_placement, "bids")[0]) - 0.01, 2
            )
            ask_price = round(
                float(orderbook.get_one(ask_placement, "asks")[0]) + 0.01, 2
            )

            if available_funds["BTC"] >= 0.001 and exec_sell == 1:
                resp = transaction_api.place_order(
                    "BTCPLN", "sell", str(available_funds["BTC"]), ask_price
                )
                if isinstance(resp, dict) and "success" in resp.keys():
                    activity_indicator += "s"
                    # TODO: logging instead of printing
                    # print('Order placed', resp['side'], resp['product_id'], resp['size'], 'at', resp['price'])
                    database.put_placed_order(
                        (
                            resp["order_params"]["order_id"],
                            resp["order_params"]["market"],
                            resp["order_params"]["type"],
                            resp["order_params"]["amount"],
                            resp["order_params"]["rate"],
                            resp["time"],
                            current_strategy,
                        )
                    )
                else:
                    # activity_indicator = 'S'
                    print("No luck selling!", resp)

            if available_funds["PLN"] > 10 and exec_buy == 1:
                amt = round((available_funds["PLN"] - 5) / float(bid_price), 6)
                resp = transaction_api.place_order("BTCPLN", "buy", str(amt), bid_price)
                if isinstance(resp, dict) and "success" in resp.keys():
                    activity_indicator += "b"
                    # print('Order placed', resp['side'], resp['product_id'], resp['size'], 'at', resp['price'])
                    database.put_placed_order(
                        (
                            resp["order_params"]["order_id"],
                            resp["order_params"]["market"],
                            resp["order_params"]["type"],
                            resp["order_params"]["amount"],
                            resp["order_params"]["rate"],
                            resp["time"],
                            current_strategy,
                        )
                    )
                else:
                    # activity_indicator = 'B'
                    print("No luck buying!", resp)
            # finished placing trades

            if time.time() > next_newline_time:
                print("")
                print(time.ctime(), end=" ")
                next_newline_time += newline_timeout

            hi_bid = float(orderbook.get_one(0, "bids")[0])
            my_balances = {
                "PLN": available_funds["PLN"],
                "BTC": available_funds["BTC"],
                "TOT": float(available_funds["PLN"]) + float(available_funds["BTC"]) * hi_bid,
                "calc_price_highest_bid": hi_bid,
            }
            save_stats(
                globals(),
                stats_file_name,
                "current_strategy",
                "ask_price",
                "bid_price",
                "my_balances",
            )
            print(activity_indicator, sep="", end="", flush=True)
            del orderbook
        except api.data.EmptyData as err:
            database.put_error(err, int(time.time()))

    except api.pycurl.error as e:
        if e.args[0] not in error_stats.keys():
            error_stats[e.args[0]] = 1
        else:
            error_stats[e.args[0]] += 1
        db_id = database.put_error(e, int(time.time()))
        print(e)
        print("error counts:", error_stats)
        if e.args[0] == 7 and e.args[1].split()[4] in [
            p["ip"] for h, p in PROXIES.items()
        ]:
            print("PROXY REFUSED CONNECTION - SWITCHING TO OWN ADDRESS")
            cryptowatch_api.remove_proxy()
            transaction_api.remove_proxy()
            communicator.send_message(
                "Proxy at {} refused connection.\n switching to own IP \n".format(
                    e.args[1].split()[4]
                )
            )
        elif e.args[0] in (6, 7):
            pass  # wait for the network to get up maybe
        elif e.args[0] == 28 and error_stats[28] < 10:
            pass  # don't send an email on an occasional timeout
        elif e.args[0] == 28 and error_stats[28] == 10:
            cryptowatch_api.reset_connection()
            transaction_api.reset_connection()
            communicator.send_message("Timeout occured. Reseting connections")
        else:
            preface = "pycurl"
            tb_str = "\n".join(traceback_format(e.__traceback__))
            communicator.send_error(
                "{}  error: {} occurred.\n Error stats are \n{}\nDB log ID is: {}\nHere is traceback: {}".format(
                    preface, str(e), str(error_stats), str(db_id), tb_str
                )
            )
    except KeyboardInterrupt:
        wrap_up()
        exit(0)
    except Exception as e:
        print(e)
        db_id = database.put_error(e, int(time.time()))
        error_stats["otherErrors"] += 1
        print("error counts:", error_stats)
        if isinstance(e, api.NotJSON):
            preface = "Not a JSON"
        else:
            preface = "some other"
        tb_str = "\n".join(traceback_format(e.__traceback__))
        communicator.send_error(
            "{}  error: {} occurred.\n Error stats are \n{}\nDB log ID is: {}\nHere is traceback: {}".format(
                preface, str(e), str(error_stats), str(db_id), tb_str
            )
        )
    else:
        error_stats["noErrors"] += 1
        if 100 == error_stats["noErrors"]:
            error_stats = {"otherErrors": 0, "noErrors": 0, "NotJSON": 0}
    finally:
        try:
            database.commit()
            time.sleep(10)
        except KeyboardInterrupt:
            wrap_up()
            exit(1)

msg = "Too many errors. Stopping script"
print(msg)
communicator.send_message(msg)
wrap_up()
