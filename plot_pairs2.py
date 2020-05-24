import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.dates as md
import numpy as np
from datetime import datetime as dt
from calendar import monthrange
import math
import sys
import argparse

date_start = "2016-10-01"
date_end = "2018-04-01"

pre_th_start = date_start
pre_th_end = "2017-06-01"

post_th_start = "2017-07-01"
post_th_end = date_end

lf_file = "n_int_20200211-094023.csv"


def main():
    parser = argparse.ArgumentParser(description="Plot IBD pair rates.")
    parser.add_argument("file_names", metavar="Pair csvs", type=str, nargs="+",
        help=".csv viles of format run,tot,pairs of IBD pairs per run")
    parser.add_argument("--monthly", dest="plot_pairs", action="store_const",
        const=plot_monthly, default=plot_periods,
        help="Plot pair rate monthly (default: plot in distinct periods)")

    args = parser.parse_args()
    fig, ax1 = plt.subplots()

    for file_name in args.file_names:
        args.plot_pairs(file_name,ax1)

    # lf_skreact = pd.read_csv("lf_20191107-005242.csv")
    lf_skreact = pd.read_csv(lf_file)
    lf_skreact["month"] = lf_skreact["month"].apply(
        lambda month : dt.strptime(month, "%Y-%m"))
    lf_skreact.set_index("month",inplace=True)
    # ax2 = ax1.twinx()
    # lf_skreact.loc[date_start:date_end,"n_int"].plot(
    #     ax=ax1,label="Expected SK Interactions")
    # ax1.legend(loc="upper left")
    # ax2.legend(loc="upper center")
    ax1.set_ylabel(r"N Pairs [month$^{-1}$]")
    # ax2.set_ylabel(r"N Reduced Pair Candidates [month$^{-1}$]")
    ax1.set_xlabel("")
    ax1.set_ylim(ymin=0)

    ax1.legend()
    plt.show()
    return

# Scales the pairs/s to pairs/month
def month_scale(date, pairs):
    year = date.year
    month = date.month
    return monthrange(year,month)[1]*24*60*60*pairs

# Groups pairs monthly, scaled to livetime
def plot_monthly(file_name, ax):
    raw_pairs = pd.read_csv(file_name)
    run_info = pd.read_csv("run_info.csv",index_col=0)
    runs = []
    pairs = []
    run_dur = []
    dates_unix = []
    last_run = int(raw_pairs["run"][0])
    run_pairs = 0

    # Adding up runs' pair counts
    for row in raw_pairs.itertuples():
        if(row.run == last_run):
            run_pairs += row.pairs
        else:
            # run_pairs = row.pairs
            runs.append(last_run)
            run_dur.append(run_info.loc[last_run]["time_diff"])
            pairs.append(run_pairs)
            dates_unix.append(run_info.loc[last_run]["start_time"])
            run_pairs = row.pairs
            last_run = int(row.run)

    # Assume all runs are entirely contained in the start date. TODO: fix this.
    dates = [dt.fromtimestamp(date_unix) for date_unix in dates_unix]

    pairs_df = pd.DataFrame({ 
        "run": runs,
        "pairs": pairs,
        "run_dur": run_dur,
        "date_unix": dates_unix,
        "date": dates })

    # Get rid of short runs
    # pairs_df = pairs_df[pairs_df["run_dur"] > 80000]

    freq="M"
    # Sum of pairs in a month
    grouped_pairs = pairs_df.groupby(
        [pd.Grouper(key="date", freq=freq)])["pairs"].sum()
    # Sum of run time in a month
    grouped_run_dur = pairs_df.groupby(
        [pd.Grouper(key="date", freq=freq)])["run_dur"].sum()
    # Get pairs/s from this
    grouped_pairs_err = grouped_pairs.apply(np.sqrt)
    normed_pairs = grouped_pairs.div(grouped_run_dur)
    normed_pairs_err = grouped_pairs_err.div(grouped_run_dur)
    normed_pairs.interpolate(inplace=True)

    normed_month_pairs_ls = []
    normed_month_errors_ls = []

    for date, pairs in normed_pairs.iteritems():
        normed_month_pairs_ls.append(month_scale(date, pairs))

    for date, err in normed_pairs_err.iteritems():
        normed_month_errors_ls.append(month_scale(date, err))

    normed_month_pairs = pd.Series(
        normed_month_pairs_ls, index = normed_pairs.index)
    normed_month_errors = pd.Series(
        normed_month_errors_ls, index = normed_pairs.index)

    normed_month_pairs.loc[date_start:date_end].plot(
        yerr=normed_month_errors.loc[date_start:date_end],
        ax=ax,style="-",label=file_name,capsize=5)
    return

def plot_periods(file_name, ax):
    # raw_pairs = pd.read_csv("pairs_sol_cut_extra_tight_fv.csv")
    raw_pairs = pd.read_csv(file_name)
    run_info = pd.read_csv("run_info.csv",index_col=0)
    runs = []
    pairs = []
    run_dur = []
    dates_unix = []
    last_run = int(raw_pairs["run"][0])
    run_pairs = 0

    # Adding up runs' pair counts
    for row in raw_pairs.itertuples():
        if(row.run == last_run):
            run_pairs += row.pairs
        else:
            run_pairs = row.pairs
            runs.append(last_run)
            run_dur.append(run_info.loc[last_run]["time_diff"])
            pairs.append(run_pairs)
            dates_unix.append(run_info.loc[last_run]["start_time"])
            run_pairs = row.pairs
            last_run = int(row.run)


    dates = [dt.fromtimestamp(date_unix) for date_unix in dates_unix]

    pairs_df = pd.DataFrame({ 
        "run": runs,
        "pairs": pairs,
        "run_dur": run_dur,
        "date_unix": dates_unix,
        "date": dates })

    pairs_df = pairs_df[pairs_df["run_dur"] > 80000]

    pairs_pre = pairs_df[pairs_df["date"] > pre_th_start]
    pairs_pre = pairs_df[pairs_df["date"] < pre_th_end]
    pairs_post = pairs_df[pairs_df["date"] > post_th_start]
    pairs_post = pairs_df[pairs_df["date"] < post_th_end]
    
    pairs_s_pre = pairs_pre["pairs"].sum()/pairs_pre["run_dur"].sum()
    pairs_s_post = pairs_post["pairs"].sum()/pairs_post["run_dur"].sum()

if __name__ == "__main__":
    main()