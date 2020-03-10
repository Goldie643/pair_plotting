import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.dates as md
from datetime import datetime as dt
from calendar import monthrange
import math
import sys

# raw_pairs = pd.read_csv("pairs_sol_cut_extra_tight_fv.csv")
raw_pairs = pd.read_csv(sys.argv[1])
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
# pairs_df = pairs_df[pairs_df["pairs"] > 400000]

# Need to normalise to livetime!
freq="M"
grouped_pairs = pairs_df.groupby(
    [pd.Grouper(key="date", freq=freq)])["pairs"].sum()
grouped_run_dur = pairs_df.groupby(
    [pd.Grouper(key="date", freq=freq)])["run_dur"].sum()
# grouped_pairs = grouped_pairs[grouped_pairs.map(
#     lambda x: math.sqrt(x)<0.01*x)]
# print(grouped_pairs.head())
# print(grouped_run_dur.head())
normed_pairs = grouped_pairs.div(grouped_run_dur)
normed_pairs.interpolate(inplace=True)
# normed_pairs = normed_pairs[normed_pairs.map(
#     lambda x: math.sqrt(x)<0.5*x)]

def month_scale(date, pairs):
    year = date.year
    month = date.month
    return monthrange(year,month)[1]*24*60*60*pairs

normed_month_pairs_ls = []

for date, pairs in normed_pairs.iteritems():
    normed_month_pairs_ls.append(month_scale(date,pairs))

normed_month_pairs = pd.Series(normed_month_pairs_ls, index = normed_pairs.index)

# ax = plt.gca()
# xfmt = md.DateFormatter('%Y-%m')
# ax.xaxis.set_major_formatter(xfmt)
# plt.xticks(rotation=25)
fig, ax1 = plt.subplots()
# ax1.set_ylim(bottom=0,top=10)
# print(normed_pairs)
normed_month_pairs.plot(ax=ax1,style="-",color="r",label="Reduced Pair Rate")

# lf_skreact = pd.read_csv("lf_20191107-005242.csv")
lf_skreact = pd.read_csv("n_int_20200211-094023.csv")
lf_skreact["month"] = lf_skreact["month"].apply(
    lambda month : dt.strptime(month, "%Y-%m"))
lf_skreact.set_index("month",inplace=True)
ax2 = ax1.twinx()
lf_skreact.loc["2016-10-01":"2018-04-01","n_int"].plot(ax=ax2,color="b",label="SK Interactions")
# ax1.legend(loc="upper left")
# ax2.legend(loc="upper center")
ax1.set_ylabel(r"N SK Interactions [month$^{-1}$]",color="b")
ax2.set_ylabel(r"N Reduced Pair Candidates [month$^{-1}$]",color="r")
ax1.set_xlabel("")
plt.show()
