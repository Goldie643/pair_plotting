import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.dates as md
from datetime import datetime as dt
import math

osc_params = pd.read_csv("sk-iv-fit.csv",names=["dm_21","thet_12","dm_31","thet_13"])

print(osc_params["dm_21"].mean())
print(osc_params["dm_21"].std())
