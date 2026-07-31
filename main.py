import pandas as pd
import sqlite3
from data_quality import run_checks

df = pd.read_csv("../data/user_watch_logs.csv")

# Data quality
run_checks(df)

# Convert timestamp
df["timestamp"] = pd.to_datetime(df["timestamp"])

# Sort for sessionization
df = df.sort_values(["user_id", "timestamp"])

# Sessionization (30 min gap rule)
df["prev_time"] = df.groupby("user_id")["timestamp"].shift(1)
df["time_diff"] = (df["timestamp"] - df["prev_time"]).dt.total_seconds() / 60

df["new_session"] = (df["time_diff"] > 30) | (df["time_diff"].isnull())
df["session_id"] = df.groupby("user_id")["new_session"].cumsum()

# Feature engineering
df["date"] = df["timestamp"].dt.date

# Dimensions
dim_user = df[["user_id"]].drop_duplicates()
dim_show = df[["show_id", "show_name", "genre"]].drop_duplicates()

# Fact
fact_watch = df[[
    "user_id",
    "show_id",
    "watch_time",
    "session_id",
    "date"
]]

# Load
conn = sqlite3.connect("../db/streaming.db")

dim_user.to_sql("dim_user", conn, if_exists="replace", index=False)
dim_show.to_sql("dim_show", conn, if_exists="replace", index=False)
fact_watch.to_sql("fact_watch", conn, if_exists="replace", index=False)

conn.close()

print("🚀 Streaming ETL Completed")

