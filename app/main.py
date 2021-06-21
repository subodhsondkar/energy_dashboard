from os import name
from os.path import dirname, join
from datetime import datetime
import pandas as pd

from bokeh.io import curdoc
from bokeh.layouts import column, row
from bokeh.models import ColumnDataSource, Div, Select,CheckboxButtonGroup, DateRangeSlider
from bokeh.plotting import figure
from bokeh.palettes import Category20

import time


number_of_panels = 2
active = []
labels = []

# Creating datasets
dfs = []
for idx in range(number_of_panels):
    active += [idx]
    labels += ["Solar Panel " + str(idx + 1)]
    temp_dfs = {}
    df = pd.read_csv(join(dirname(__file__), "data_" + str(idx) + ".csv"))
    df.drop("Unnamed: 0", axis=1, inplace=True)
    df["Month"] += 1
    df["Date"] += 1
    df["DateTime"] = pd.to_datetime(df["Year"].map(str) + "-" + df["Month"].map(str) + "-" + df["Date"].map(str) + " " + df["Hour"].map(str) + ":" + df["Minute"].map(str) + ":00")
    temp_dfs["Minute"] = df.loc[:, ["DateTime", "PV_Usage"]]
    df = df.groupby(["Year", "Month", "Date", "Hour"]).sum().drop("Minute", axis=1).reset_index()
    df["DateTime"] = pd.to_datetime(df["Year"].map(str) + "-" + df["Month"].map(str) + "-" + df["Date"].map(str) + " " + df["Hour"].map(str) + ":00:00")
    temp_dfs["Hour"] = df.loc[:, ["DateTime", "PV_Usage"]]
    df = df.groupby(["Year", "Month", "Date"]).sum().drop("Hour", axis=1).reset_index()
    df["DateTime"] = pd.to_datetime(df["Year"].map(str) + "-" + df["Month"].map(str) + "-" + df["Date"].map(str) + " 00:00:00")
    temp_dfs["Date"] = df.loc[:, ["DateTime", "PV_Usage"]]
    df = df.groupby(["Year", "Month"]).sum().drop("Date", axis=1).reset_index()
    df["DateTime"] = pd.to_datetime(df["Year"].map(str) + "-" + df["Month"].map(str) + "-01 00:00:00")
    temp_dfs["Month"] = df.loc[:, ["DateTime", "PV_Usage"]]
    dfs += [temp_dfs]


desc = Div(text=open(join(dirname(__file__), "description.html")).read(), sizing_mode="stretch_width")

# Create Input controls
panels = CheckboxButtonGroup(name="Selected Solar Panels", labels=labels, active=active)
interval = Select(title="Select Interval", value="Date", options=["Minute", "Hour", "Date", "Month"])
date_range = DateRangeSlider(title="Select Date Range", start=datetime(2021, 3, 1), end=datetime(2021, 3, 28), value=(datetime(2021, 3, 1), datetime(2021, 3, 28)), step=24*60*60*1000)


# Create Column Data Source that will be used by the plot
source = ColumnDataSource(data=dict(x=dfs[panels.active[0]][interval.value].loc[(dfs[panels.active[0]][interval.value]["DateTime"] >= pd.to_datetime(date_range.value[0] * (10 ** 6))) & (dfs[panels.active[0]][interval.value]["DateTime"] <= pd.to_datetime(date_range.value[1] * (10 ** 6))), "DateTime"]))
for idx in range(len(panels.active)):
    source.data['y' + str(panels.active[idx])] = dfs[panels.active[idx]][interval.value].loc[(dfs[panels.active[idx]][interval.value]["DateTime"] >= pd.to_datetime(date_range.value[0] * (10 ** 6))) & (dfs[panels.active[idx]][interval.value]["DateTime"] <= pd.to_datetime(date_range.value[1] * (10 ** 6))), "PV_Usage"]

######################## TOOLTIPS BAAKI
######################## Legend label not getting removed on panel deselection
######################## SLOW (?)
######################## Any interval requires data values to have at least 2 values for that interval
######################## Double date range
######################## Multiple graphs on same page, but intuitive
TOOLTIPS=[
    ("Date", "@x"),
    ("Solar Panel 1", "@y0"),
    ("Solar Panel 2", "@y1"),
]

p = figure(height=300, width=600, toolbar_location=None, tooltips=TOOLTIPS, sizing_mode="scale_both", title="PV Generation", x_axis_label="Date/Time", y_axis_label="PV Generation", x_axis_type="datetime")
for idx in range(len(panels.active)):
    p.line('x', 'y' + str(panels.active[idx]), source=source, color=Category20[20][panels.active[idx]], legend_label="Panel " + str(panels.active[idx] + 1), line_width=2)


def update():
    global dfs
    source.data = dict(x=dfs[panels.active[0]][interval.value].loc[(dfs[panels.active[0]][interval.value]["DateTime"] >= pd.to_datetime(date_range.value[0] * (10 ** 6))) & (dfs[panels.active[0]][interval.value]["DateTime"] <= pd.to_datetime(date_range.value[1] * (10 ** 6))), "DateTime"])
    for idx in range(len(panels.active)):
        source.data['y' + str(panels.active[idx])] = dfs[panels.active[idx]][interval.value].loc[(dfs[panels.active[idx]][interval.value]["DateTime"] >= pd.to_datetime(date_range.value[0] * (10 ** 6))) & (dfs[panels.active[idx]][interval.value]["DateTime"] <= pd.to_datetime(date_range.value[1] * (10 ** 6))), "PV_Usage"]


panels.on_change('active', lambda attr, old, new: update())
interval.on_change('value', lambda attr, old, new: update())
date_range.on_change('value', lambda attr, old, new: update())


l = column(desc, row(column(panels, interval, date_range), p), sizing_mode="stretch_width")

update()  # initial load of the data

curdoc().add_root(l)
curdoc().title = "PV Generation"
