import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.dates as md
from datetime import datetime as dt
import math

raw_pairs = pd.read_csv("pairs.csv")
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
# normed_pairs = normed_pairs[normed_pairs.map(
#     lambda x: math.sqrt(x)<0.5*x)]

# ax = plt.gca()
# xfmt = md.DateFormatter('%Y-%m')
# ax.xaxis.set_major_formatter(xfmt)
# plt.xticks(rotation=25)
fig, ax1 = plt.subplots()
normed_pairs.plot(ax=ax1,style="-",color="r")

lf_skreact = pd.read_csv("lf_20191107-005242.csv")
lf_skreact["month"] = lf_skreact["month"].apply(
    lambda month : dt.strptime(month, "%Y-%m"))
print(lf_skreact.loc)
lf_skreact.set_index("month",inplace=True)
ax2 = ax1.twinx()
lf_skreact.loc["2016-01-01":"2018-04-01","p/r2"].plot(ax=ax2,color="b")
plt.show()