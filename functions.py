from __future__ import generator_stop
import time
import subprocess


def max_dict_val(dct):
    return max([dct[k] for k in dct])


def catchup_multi(
    api_collection, db_collection, frequency_collection, show_output=False
):
    """

    :param api_collection: a tuple of api objects to fetch history for
    :param db_collection: a tuple of database objects in the same order as api objects
    :param frequency_collection: number of seconds between allowed calls of each api object. Can be fractonal
    :param show_output: whether to print a table showing the progress of download
    :return: some meaningless number
    """
    rounds = 0
    data_generators = ()
    execution_times = []
    for market in zip(api_collection, db_collection):
        last_trade = market[1].get_last_trade()[0]
        data_generators += (market[0].get_public_history(last_trade),)
        execution_times += [0]
    t0 = time.time()
    markets = list(zip(data_generators, db_collection, frequency_collection))
    rows_inserted = {
        market[0].gi_frame.f_locals["self"].__class__.__name__: 0 for market in markets
    }
    total_rows_inserted = {
        market[0].gi_frame.f_locals["self"].__class__.__name__: 0 for market in markets
    }
    while len(markets) != 0:
        i = 0
        for market in markets:
            try:
                if time.time() > execution_times[i] + market[2]:
                    exchange_name = (
                        market[0].gi_frame.f_locals["self"].__class__.__name__
                    )
                    operation_time = time.time()
                    data_object = next(market[0])  # this is where the trades are pulled
                    pull = round(time.time() - operation_time, 3)
                    operation_time2 = time.time()
                    rows_inserted[exchange_name] = market[1].put_trades(
                        data_object.as_tuples(), bulk=True
                    )
                    # print(market[1].cursor.statement)  # Temporary
                    market[1].put_turnaround(data_object.as_rtt())
                    total_rows_inserted[exchange_name] += rows_inserted[exchange_name]
                    execution_times[i] = time.time()
                    insert = round(time.time() - operation_time2, 3)
                    overall = round(time.time() - t0, 3)
                    t0 = time.time()
                    if show_output:
                        print(
                            "{:^20}|{:^30}|{:^10}|{:^10}|{:^10}|{:^10}".format(
                                "exch", "time", "pull", "insert", "cycle", "tot rows"
                            )
                        )
                        print(
                            "{:^20}|{:^30}|{:^10}|{:^10}|{:^10}|{:^10}".format(
                                exchange_name,
                                time.ctime(),
                                pull,
                                insert,
                                overall,
                                total_rows_inserted[exchange_name],
                            )
                        )
                        print("-" * 95)
                    if rows_inserted[exchange_name] < 90:
                        market[0].close()
                        markets.remove(market)
                i += 1
            except StopIteration:
                markets.remove(market)
        rounds += 1
        time.sleep(0.05)
    return total_rows_inserted


def catchup_placed_trades(db, api, data_structure):
    start = 0
    db_trades = db.count_placed_trades()[0][0]
    response = api.get_trade_history("BTCPLN", start)
    all_trades = response["data"]["total"]
    while db_trades < all_trades:
        db.insert_placed_trades(response["data"]["results"], data_structure)
        db.commit()
        start += 1000
        db_trades = db.count_placed_trades()[0][0]
        response = api.get_trade_history("BTCPLN", start)
        all_trades = response["data"]["total"]
    if db_trades > all_trades:
        raise Exception("Impossible: More trades in db than in api!")


def set_my_vars(file_name, global_vars):
    """read variable names and values from a file and set variables in program to those values

    file must have the following format
    (whitespace at both ends of the line is ignored)
    (whitespace on both sides of equals sign is ignored)
    # a comment
    variablename = 12

    only use values that convert to float ot int
    """
    with open(file_name, "r") as f:
        t = f.read().splitlines()
    set_count = 0
    for l in t:
        if l.strip() != "" and "#" != l.strip()[0]:
            vname, sep, val = [x.strip() for x in l.strip().partition("=")]
            # precaution - any variables to be set must be initialized earlier
            if vname in global_vars:
                val = float(val)
                if int(val) == val:
                    global_vars[vname] = int(val)
                else:
                    global_vars[vname] = float(val)
                set_count += 1
    return set_count


def save_stats(globalvars, filepath, *varnames):
    """save variables and their values to file
    provide varnames as additional positional parameters"""
    if varnames is not None:
        with open(filepath, "w") as f:
            s = time.ctime() + "\n\n"
            f.write(s)
            for name in varnames:
                s = name + ":\t" + str(globalvars[name]) + "\n"
                f.write(s)


def printvariables(globalvars, *varnames):
    """print variables and their values
    provide varnames as additional positional parameters"""
    if 1 == globalvars["printstats"] and varnames is not None:
        print("")
        print("---")
        for name in varnames:
            print(name, globalvars[name])


def is_proxy_running(port_number):
    """
        this is no longer needed - only used it when proxy was done with ssh tunnelling from localhost.
        With proper proxy software in our cloud we will just assume that it's running, or act upon exception
    """
    port_number_string = str(port_number)
    port = "[{}]{}".format(port_number_string[0], port_number_string[1:])
    process_count = subprocess.check_output(
        "ps -eo pid,cmd|grep [s]sh|grep {}|wc -l".format(port), shell=True
    ).decode("utf-8")[:-1]
    if 0 < int(process_count):
        return True
    else:
        return False
