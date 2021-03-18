#!/usr/bin/env python3
# -*- coding: utf-8 -*-


def archive_orderbook(db, pair, data):
    """
    archive the entire orderbook in the orderbookArchive table
    :param db:object
    :param pair: 'BTCEUR'  etc.
    :param data: payload data
    :return: int
    """
    queryString = """
        INSERT IGNORE INTO `orderbookArchive{0}`
        ( `orderType`,
        `price`,
        `amount`,
        `orderCount`,
        `orderTimeStamp`,
        `step`)
        VALUES(%s, %s, %s, %s, %s, %s);
    """.format(pair)
    db.executemany(queryString, data)
    return db.rowcount


def get_max_time_stamp(db, pair):
    queryString = """
            SELECT orderTimeStamp
            FROM orderbookArchive{0}
            WHERE
            id = (SELECT count(*) FROM  orderbookArchive{0});
        """.format(pair)
    db.execute(queryString)
    return db.fetchone()


def get_payload(db, pair, cutoff):
    """Gets a subset of orderbook rows
    one per minute of time
    :param db:database cursor
    :param pair: 'BTCEUR'  etc.
    :param cutoff:unix timestamp telling where to start pulling data
    :return: list of tuples representing data

    """
    if cutoff is None:
        cutoff = (0, )

    queryString = """
        SELECT
            `orderType`,
            `price`,
            `amount`,
            `orderCount`,
            `orderTimeStamp`,
            `step`
        FROM
            `orderbook{0}` dt
        INNER JOIN
        (
            SELECT min(`orderTimestamp`) firstOfBatch
            FROM `orderbook{0}`
            GROUP BY
            (`orderTimeStamp` div 60)
        ) t
        ON dt.orderTimeStamp = t.firstOfBatch
        WHERE orderTimeStamp > %s
        ORDER BY orderTimeStamp ASC
            , orderType
            , step ASC;
    """.format(pair)
    db.execute(queryString, cutoff)
    return db.fetchall()


def clean_orderbook(db, pair, keep_time_hours):
    """
    remove orderbook records older than 2nd parameter given as 
    "number of hours ago"
    """
    present = time.time()
    queryString = "DELETE FROM orderbook{0} WHERE orderTimeStamp < %s;".format(pair)
    timeParam = present - 3600 * keep_time_hours
    db.execute(queryString, [timeParam])
    return db.rowcount


def get_max_trade_timestamp(db, pair):
    queryString = """
                SELECT MAX(tradeTimeStamp) FROM `tradeArchive` 
                WHERE ticker = %s
            """
    db.execute(queryString, (pair,))
    return db.fetchone()


def get_trade_payload(db, pair, timestamp):
    # if timestamp is None:
    #     timestamp = 0
    queryString = """
                SELECT (0) `ticker`,
                    `tradeId`,
                    `tradeType`,
                    `price`,
                    `amount`,
                    `tradeTimeStamp`
                FROM `trade{0}` 
                WHERE tradeTimeStamp >= %s
            """.format(pair)
    db.execute(queryString, timestamp)
    return db.fetchone()

def archive_trade(db, pair, data):
    """
    archive the entire trades in the tradeArchive table
    :param db:object
    :param pair: 'BTCEUR'  etc.
    :param data: payload data
    :return: int
    """
    queryString = """
        INSERT INTO `tradearchive`
        (
        ticker
        , tradeId
        , tradeType
        , price
        , amount
        , tradeTimeStamp)
        VALUES(%s, %s, %s, %s, %s, $s);
    """.format(pair)
    db.executemany(queryString, data)
    return db.rowcount


def clean_trade(db, pair, keep_time_hours):
    """
    remove trades records older than 2nd parameter given as
    "number of hours ago"
    """
    present = time.time()
    queryString = "DELETE FROM trade{0} WHERE orderTimeStamp < %s;".format(pair)
    timeParam = present - 3600 * keep_time_hours
    db.execute(queryString, [timeParam])
    return db.rowcount

############
#   BEGIN   #
#############

import mysql.connector as mariadb
import time

def Raspcon(user, password,database):
    con = mariadb.connect(user = user, password = password , database = database)
    concur = con.cursor()
    return con, concur

def Arubacon(user, password,database):
    con = mariadb.connect(user = user, password = password , database = database,
        host='1.1.1.1', port=3306)
    concur = con.cursor()
    return con, concur


bases = {'gdax': ('BTCEUR','LTCEUR','ETHEUR'), 'kraken': ('BTCEUR','LTCEUR','ETHEUR')}
for base in bases:
    rasp_con, rasp_cur = Raspcon('root', '', base)
    arub_con, arub_cur = Arubacon('user', 'pass', base)
    for pair in bases[base]:
        rowsArchived = archive_orderbook(arub_cur, pair, get_payload(rasp_cur, pair,
                        get_max_time_stamp(arub_cur, pair)))
        if rowsArchived > 20:
            rowsRemoved = clean_orderbook(rasp_cur, pair, 24)
        else:
            rowsRemoved = 0
        print(rowsArchived, "rows added to archive.", pair)
        print(rowsRemoved, "rows removed from orderbook.", pair)
        rowsArchived = archive_trade(arub_cur, pair, get_trade_payload(rasp_cur, pair,
                        get_max_trade_timestamp(arub_cur, pair)))
        if rowsArchived > 20:
            rowsRemoved = clean_trade(rasp_cur, pair, 24)
        else:
            rowsRemoved = 0
        print(rowsArchived, "rows added to archive.", pair)
        print(rowsRemoved, "rows removed from orderbook.", pair)

    rasp_cur.close()
    arub_cur.close()



