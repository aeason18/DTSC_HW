import pandas as pd
from pathlib import Path

DATA_DIR = Path(__file__).parent

SEASON_FILES = {
    "2020-21": "E0_2021.csv",
    "2021-22": "E0_2122.csv",
    "2022-23": "E0_2223.csv",
    "2023-24": "E0_2324.csv",
    "2024-25": "E0_2425.csv",
    "2025-26": "E0_2526.csv",
}

KEEP_COLS = [
    "Date", "HomeTeam", "AwayTeam",
    "FTHG", "FTAG", "FTR",
    "HTHG", "HTAG", "HTR",
    "Referee",
    "HS", "AS", "HST", "AST",
    "HF", "AF", "HC", "AC",
    "HY", "AY", "HR", "AR",
]

frames = []
for season, fname in SEASON_FILES.items():
    df = pd.read_csv(DATA_DIR / fname, encoding="utf-8-sig")
    cols = [c for c in KEEP_COLS if c in df.columns]
    df = df[cols].copy()
    df["Season"] = season
    frames.append(df)

combined = pd.concat(frames, ignore_index=True)
combined["Date"] = pd.to_datetime(combined["Date"], dayfirst=True, errors="coerce")
combined = combined.dropna(subset=["HomeTeam", "AwayTeam", "FTHG", "FTAG"])

rename = {
    "FTHG": "HomeGoals", "FTAG": "AwayGoals", "FTR": "FullTimeResult",
    "HTHG": "HomeGoalsHT", "HTAG": "AwayGoalsHT", "HTR": "HalfTimeResult",
    "HS": "HomeShots", "AS": "AwayShots",
    "HST": "HomeShotsOnTarget", "AST": "AwayShotsOnTarget",
    "HF": "HomeFouls", "AF": "AwayFouls",
    "HC": "HomeCorners", "AC": "AwayCorners",
    "HY": "HomeYellow", "AY": "AwayYellow",
    "HR": "HomeRed", "AR": "AwayRed",
}
combined = combined.rename(columns=rename)
combined["TotalGoals"] = combined["HomeGoals"] + combined["AwayGoals"]

out_path = DATA_DIR / "premier_league_matches.csv"
combined.to_csv(out_path, index=False)
print(f"Wrote {len(combined)} rows to {out_path}")
print(combined["Season"].value_counts())
