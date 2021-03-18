#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Foreword for reviewers @hummingbird
I've developed this script to trade BTC/EUR, with a veiw to add more pairs later on
The catchup_multi function was a start to go towards that end. Please tee tests for a sample uf intended usage
Don't look for strategies class/module it's not deleted, I just never came up with anything sensible.
Public apis should work out of the box
"""

# from functions import * #import objects here
import api
import db
import comm
from config import *
from functions import *
from traceback import format_tb as traceback_format


def wrap_up():
    for a in exchange_apis:
        a.close()
    print("")
    print("-" * 15)
    print("closed Api connections")
    for b in databases:
        b.commit()
        b.close()
    print("closed db connections")
    print(time.ctime())
    print("<---- QUITTING ---->")


"""
start cryptowatch
- make an api object
- make a db object
- query api and insert into db in a loop
"""

exchange_apis = (api.GdaxPublic(), api.KrakenPublic())

databases = (
    db.Gdax(DB_USER, DB_PASSWORD, dbname='gdax', dbhost='localhost', unix_socket='/var/run/mysqld/mysqld.sock'),
    db.Kraken(DB_USER, DB_PASSWORD, dbname='kraken', dbhost='localhost', unix_socket='/var/run/mysqld/mysqld.sock')
)


entities = list(zip(exchange_apis, databases))

stats_file_name = '/dev/shm/bot.stats'
communicator = comm.Comm('orderbook_gather', 'gilmijar@gmail.com')


t0 = time.time()
activity_indicator = "."
newline_timeout = 240
next_newline_time = time.time()
orders_save_timeout = 30
next_orders_save_time = 0
error_stats = {"otherErrors": 0, "noErrors": 0}

while 100 > max_dict_val(error_stats):
    for exchange_api, database in entities:
        try:
            n = set_my_vars("settings.txt", globals())

            try:
                orderbook = exchange_api.get_order_book()
                database.put_turnaround(orderbook.as_rtt())
                # only save orders once every N seconds
                if next_orders_save_time < time.time():
                    database.put_orders(orderbook.as_tuples(inner=100))
                    next_orders_save_time = time.time() + orders_save_timeout
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
                exchange_api.remove_proxy()
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
                exchange_api.reset_connection()
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
            database.commit()
    try:
        time.sleep(10)
    except KeyboardInterrupt:
        wrap_up()
        exit(1)

msg = "Too many errors. Stopping script"
print(msg)
communicator.send_message(msg)
wrap_up()
