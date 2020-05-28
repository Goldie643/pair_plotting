import pandas as pd
from collections import namedtuple
import matplotlib.pyplot as plt
import matplotlib.dates as md
import matplotlib.patches as mpatches
import numpy as np
import datetime as dt
from datetime import date
from calendar import monthrange
import math
import sys
import argparse

rate = 7 # Fraction of day to give rate in
online_eff = 0.17*0.428

date_start = "2016-10"
date_end = "2018-04"

pre_th_start = date_start
pre_th_end = "2017-06"

post_th_start = "2017-07"
post_th_end = date_end

lf_file = "n_int_20200211-094023.csv"

sk_iv_online_e = 0.57167 # Efficiency of detection of sk-iv reactor e+
n_cap_e = 0.17 # Efficiency of detection of 2.2 MeV gamma
sk_iv_ibd_e = sk_iv_online_e*n_cap_e



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

    # Get start and end date of each era INCLUSIVE
    pre_period = (args.unblind[:7],args.unblind[-7:])
    post_period = (args.blind[:7],args.blind[-7:])

    def add_months(sourcedate, months):
        month = sourcedate.month - 1 + months
        year = sourcedate.year + month // 12
        month = month % 12 + 1
        day = min(sourcedate.day, monthrange(year,month)[1])
        return dt.date(year, month, day)
    
    pre_period_dt = [
        date(int(pre_period[0][:4]),int(pre_period[0][5:8]),1),
        date(int(pre_period[1][:4]),int(pre_period[1][5:8]),1)
        ]
    pre_period_dt[1] = add_months(pre_period_dt[1],1)
    pre_period_dur = pre_period_dt[1] - pre_period_dt[0]

    post_period_dt = [
        date(int(post_period[0][:4]),int(post_period[0][5:8]),1),
        date(int(post_period[1][:4]),int(post_period[1][5:8]),1)
        ]
    post_period_dt[1] = add_months(post_period_dt[1],1)
    post_period_dur = post_period_dt[1] - post_period_dt[0]

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

    raw_pairs = pd.read_csv(args.file)
    run_info = pd.read_csv("run_info.csv",index_col=0)
    runs = []
    pairs = []
    tots = []
    run_dur = []
    dates_unix = []
    last_run = int(raw_pairs["run"][0])
    run_pairs = 0
    run_tots = 0

    # Adding up runs' pair counts
    for row in raw_pairs.itertuples():
        if(row.run == last_run):
            run_pairs += row.pairs
            run_tots += row.tot
        else:
            run_pairs = row.pairs
            runs.append(last_run)
            run_dur.append(run_info.loc[last_run]["time_diff"])
            pairs.append(run_pairs)
            tots.append(run_tots)
            dates_unix.append(run_info.loc[last_run]["start_time"])
            run_pairs = row.pairs
            run_tots = row.tot
            last_run = int(row.run)

    dates = [dt.datetime.fromtimestamp(date_unix) for date_unix in dates_unix]

    pairs_df = pd.DataFrame({ 
        "run": runs,
        "pairs": pairs,
        "tot": tots,
        "run_dur": run_dur,
        "date_unix": dates_unix,
        "date": dates })

    # Get rid of short runs
    pairs_df = pairs_df[pairs_df["run_dur"] > 80000]

    pairs_pre = pairs_df[pairs_df["date"] >= pre_period[0]]
    pairs_pre = pairs_df[pairs_df["date"] <= pre_period[1]]
    livetime_pre = pairs_pre["run_dur"].sum()
    livetime_post = 1 #

    # Normalised pairs/s
    pairs_s_pre = pairs_pre["pairs"].sum()/livetime_pre
    pairs_s_pre_tot = pairs_pre["tot"].sum()/livetime_pre
    pairs_s_pre *= 60*60*24
    pairs_s_pre_tot *= 60*60*24

    # This is blinded
    # pairs_post = pairs_df[pairs_df["date"] > post_period[0]]
    # pairs_post = pairs_df[pairs_df["date"] < post_period[1]]
    # livetime_post = pairs_post["run_dur"].sum()
    # pairs_s_post = pairs_post["pairs"].sum()/livetime_post

    # Get expected int in each era
    skreact = pd.read_csv(lf_file)
    skreact["month"] = skreact["month"].apply(
        lambda month : dt.datetime.strptime(month, "%Y-%m"))
    skreact_pre = skreact[skreact["month"] >= pre_period[0]]
    skreact_pre = skreact_pre[skreact_pre["month"] <= pre_period[1]]
    skreact_post = skreact[skreact["month"] >= post_period[0]]
    skreact_post = skreact_post[skreact_post["month"] <= post_period[1]]

    skreact_s_pre = skreact_pre["n_int"].sum()/pre_period_dur.days
    skreact_s_post = skreact_post["n_int"].sum()/post_period_dur.days

    skreact_s_pre *= rate
    skreact_s_post *= rate
    pairs_s_pre *= rate
    
    print("Pre-TH n days: %i" % pre_period_dur.days)
    print("Post-TH n days: %i" % post_period_dur.days)

    print()

    print("SKREACT:")
    print("Pre-TH " + pre_th_start + " to " + pre_th_end + 
        " (%i days):" % pre_period_dur.days)
    print("----Interacted------------------------")
    print("%f [/%.2f days]" % (skreact_s_pre,rate))
    print("%f Total" % skreact_pre["n_int"].sum())
    print("----Detected--------------------------")
    print("%f [/%.2f days]" % (skreact_s_pre*online_eff,rate))
    print("%f Total" % (skreact_pre["n_int"].sum()*online_eff))
    print()

    print("Post-TH " + post_th_start + " to " + post_th_end + 
        " (%i days):" % post_period_dur.days)
    print("----Interacted------------------------")
    print("%f [/%.2f days]" % (skreact_s_post,rate))
    print("%f Total" % skreact_post["n_int"].sum())
    print("----Detected--------------------------")
    print("%f [/%.2f days]" % (skreact_s_post*online_eff,rate))
    print("%f Total" % (skreact_post["n_int"].sum()*online_eff))
    print()

    print("DATA PRE:")
    print("Pre-TH (cut): %f [/%.2f days]" % (pairs_s_pre,rate))
    print("Pre-TH (online+offline co): %f [/%.2f days]" % (pairs_s_pre_tot,rate))

    bg_s_pre = pairs_s_pre - skreact_s_pre

    solar_n_mc = 0.6313
    solar_e_mc = 0.006941
    solar_mc_e = solar_n_mc*solar_e_mc

    solar_mc_e = 0.00248457 # From reactor_red stuff

    print("Solar cut signal efficiency = %f" % solar_mc_e)

    solar_n_bg = 0.4821
    solar_e_bg = 0.0008456
    solar_bg_e = solar_n_bg*solar_e_bg

    solar_bg_e = 0.00050402

    print("Solar cut bg efficiency = %f" % solar_bg_e)

    exit()

    Cut = namedtuple("Cut", ["name", "bg_e", "sg_e"])
    cuts = [
        # Cut("Raw",1,1),
        Cut("SK-IV Solar",solar_bg_e,solar_mc_e),
        # Cut("CNN",0.00005,0.8)
    ]

    bar_width = 0.25
    bar_gap = 0.00
    group_gap = 0.01
    group_width = bar_width*len(cuts)
    bar_x = 0

    bg_rates = [] # For formatting the plot


    for cut in cuts:
        # Pre

        pre_bg_cut = cut.bg_e*bg_s_pre
        plt.bar(bar_x, pre_bg_cut, bar_width, color="C0", label=cut.name)
        plt.bar(bar_x, cut.sg_e*skreact_s_pre, bar_width, color="C1",
            bottom=pre_bg_cut)

        bar_x += bar_width + bar_gap

        # Post
        post_bg_cut = cut.bg_e*bg_s_pre
        plt.bar(bar_x, post_bg_cut, bar_width, color="C0", 
            label=cut.name)
        plt.bar(bar_x, cut.sg_e*skreact_s_post, bar_width, 
            color="C1", bottom=post_bg_cut)

        bg_rates.append(post_bg_cut)

        bar_x+=bar_width + group_gap

    plt.xticks([bar_width*(2*x+0.5)+x*group_gap for x in range(len(cuts))],
        [cut.name for cut in cuts])

    sg_patch = mpatches.Patch(color="C1", label="Signal")
    bg_patch = mpatches.Patch(color="C0", label="BG")
    ax1.legend(handles=[sg_patch,bg_patch])

    # plt.ylim(bottom=min(bg_rates)-10)
    plt.show()

    return

# Scales the pairs/s to pairs/month
def month_scale(date, pairs):
    year = date.year
    month = date.month
    return monthrange(year,month)[1]*24*60*60*pairs

if __name__ == "__main__":
    main()
