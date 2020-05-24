import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.dates as md
import numpy as np
from datetime import datetime as dt
from calendar import monthrange
import math
import sys
import argparse

date_start = "2016-10"
date_end = "2018-04"

pre_th_start = date_start
pre_th_end = "2017-06"

post_th_start = "2017-07"
post_th_end = date_end

lf_file = "n_int_20200211-094023.csv"

bar_width = 0.25

def main():
    parser = argparse.ArgumentParser(description="Plot IBD pair rates.")
    parser.add_argument("file", metavar="Pair csv", type=str,
        help=".csv file of format run,tot,pairs of IBD pairs per run")
    parser.add_argument("--unblind", type=str, 
        default=pre_th_start+"-"+pre_th_end,
        help="Period to extrapolate from in YYYY-MM_YYYY-MM format.")
    parser.add_argument("--blind", type=str,
        default=post_th_start+"-"+post_th_end,
        help="Period to extrapolate to in YYYY-MM_YYYY-MM format.")
    # parser.add_argument("--monthly", dest="plot_pairs", action="store_const",
    #     const=plot_monthly, default=plot_periods,
    #     help="Plot pair rate monthly (default: plot in distinct periods)")

    args = parser.parse_args()

    fig, ax1 = plt.subplots()

    # Select only unblinded period in pairs
    # Get total pairs in period from tot column
    # Normalise (/week might be nice) using run info
    # Get same normalised number from skreact info
    # Minus off from total, you now have raw BG rate
    # and signal rate
    # Extrapolate to post: use same BG rate, add on 
    # new skreact rate
    # Get bg and signal efficiency from traditional cuts/CNN
    # Multiply the pre/post bg/signal rates by this to get pre/post
    # cut rates.

    pre_period = (args.unblind[:7],args.unblind[-7:])
    post_period = (args.blind[:7],args.blind[-7:])

    lf_skreact = pd.read_csv(lf_file)
    lf_skreact["month"] = lf_skreact["month"].apply(
        lambda month : dt.strptime(month, "%Y-%m"))
    lf_skreact.set_index("month",inplace=True)
    ax1.set_ylabel(r"N Pairs [month$^{-1}$]")
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
