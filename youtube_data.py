import pandas as pd
import numpy as np


COLOR = "#f2AAAA"


def load_watch_history(path_or_buf: str, timezone: str) -> pd.DataFrame:
    """Create the watch dataframe from a path or a json string"""

    # Load the data
    df = pd.read_json(path_or_buf)

    # Extract the channelname
    df["channel"] = df["subtitles"].map(
        lambda x: x[0]["name"] if type(x) is list else "unknown"
    )

    # Set the datetime to the right type
    df["time"] = pd.to_datetime(df["time"], infer_datetime_format=True)
    df["time"] = df["time"].map(lambda x: x.astimezone(timezone))

    # Drop all unneeded columns
    df = df[["title", "channel", "time"]]
    return df


def load_search_history(path_or_buf: str, timezone: str) -> pd.DataFrame:
    """Create the search dataframe from a path or a json string"""

    # Load the data
    df = pd.read_json(path_or_buf)

    # Set the datetime to the right type
    df["time"] = pd.to_datetime(df["time"], infer_datetime_format=True)
    df["time"] = df["time"].map(lambda x: x.astimezone(timezone))

    # Drop all unneeded columns
    df = df[["title", "time"]]

    return df


def creator_plot(watch: pd.DataFrame, number: int):
    df = watch["channel"].value_counts()
    df.drop(["unknown"], inplace=True)
    df = df.head(number).sort_values()
    plot = df.plot(kind="barh", color=COLOR, figsize=[6.4, number * 0.28])
    plot.set_xlabel("videos watched")
    plot.set_title(f"Top {number} creators")
    return plot


def watch_timeline_plot(watch: pd.DataFrame):
    df = pd.DataFrame(watch["time"])
    df.set_index("time", inplace=True)
    df["amount"] = 1
    df = df.resample("W").count()
    plot = df.plot(color=COLOR)
    plot.set_title("Video Timeline")
    plot.set_ylim(ymin=-0.03 * df["amount"].max())
    plot.set_ylabel("videos watched per week")
    plot.set_xlabel("")
    plot.get_legend().remove()
    return plot


def watch_month_plot(watch: pd.DataFrame):
    df = pd.DataFrame()
    df["time"] = watch["time"]
    df["amount"] = 1
    df = df.groupby(df["time"].dt.month).sum()
    df = df.reindex(range(1, 13)).fillna(0)
    df.index = df.index.map(lambda x: calendar.month_abbr[x])
    plot = df.plot(kind="bar", color=COLOR)
    plot.set_title("Videos watched per month")
    plot.set_ylabel("")
    plot.set_xlabel("")
    plot.get_legend().remove()
    return plot


def watch_week_plot(watch: pd.DataFrame):
    df = pd.DataFrame()
    df["time"] = watch["time"]
    df["amount"] = 1
    df = df.groupby(df["time"].dt.dayofweek).sum()
    df = df.reindex(range(0, 7)).fillna(0)
    df.index = df.index.map(lambda x: calendar.day_abbr[x])
    plot = df.plot(kind="bar", color=COLOR)
    plot.set_title("Videos watched per weekday")
    plot.set_ylabel("")
    plot.set_xlabel("")
    plot.get_legend().remove()
    return plot


def watch_hour_plot(watch: pd.DataFrame):
    df = pd.DataFrame()
    df["time"] = watch["time"]
    df["amount"] = 1
    df = df.groupby(df["time"].dt.hour).sum()
    df = df.reindex(range(0, 24)).fillna(0)
    df.index = df.index.map(lambda x: f"{x:02}:00")
    plot = df.plot(kind="bar", color=COLOR)
    plot.set_title("Videos watched per hour")
    plot.set_ylabel("")
    plot.set_xlabel("")
    plot.get_legend().remove()
    return plot


def search_timeline_plot(search: pd.DataFrame):
    df = pd.DataFrame(search["time"])
    df.set_index("time", inplace=True)
    df["amount"] = 1
    df = df.resample("W").count()
    plot = df.plot(color=COLOR)
    plot.set_title("Searches Timeline")
    plot.set_ylim(ymin=-0.03 * df["amount"].max())
    plot.set_ylabel("Searches per week")
    plot.set_xlabel("")
    plot.get_legend().remove()
    return plot


def searchword_plot(search: pd.DataFrame, number: int):
    # Create a dataframe where the word column has in every row just a single word
    df = pd.DataFrame(search["title"])
    df = pd.DataFrame(df.title.str.split(" ").tolist()).stack()
    df = df.reset_index(0)
    df.columns = ["tmp", "word"]
    df = df.reset_index(0)
    df = pd.DataFrame(df.word)
    df["word"].replace("", np.nan, inplace=True)
    df.dropna(subset=["word"], inplace=True)

    # Create the plot
    df = df["word"].value_counts()
    df = df[df < len(search) * 0.9]
    df = df.head(number).sort_values()
    plot = df.plot(kind="barh", figsize=[6.4, number * 0.28], color=COLOR)
    plot.set_title(f"Top {number} searchwords")
    return plot

