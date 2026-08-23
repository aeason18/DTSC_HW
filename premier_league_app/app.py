import pandas as pd
import plotly.express as px
import streamlit as st

st.set_page_config(page_title="Premier League EDA", page_icon="⚽", layout="wide")

DATA_PATH = "data/premier_league_matches.csv"


@st.cache_data
def load_data(path: str) -> pd.DataFrame:
    df = pd.read_csv(path, parse_dates=["Date"])
    return df


df = load_data(DATA_PATH)

st.title("⚽ Premier League Match Data Explorer")
st.caption(
    "Match-level results and stats for the last 6 Premier League seasons "
    "(2020-21 through 2025-26), sourced from football-data.co.uk."
)

# ---------- Sidebar filters ----------
st.sidebar.header("Filters")
seasons = sorted(df["Season"].unique())
selected_seasons = st.sidebar.multiselect("Season", seasons, default=seasons)

all_teams = sorted(set(df["HomeTeam"]) | set(df["AwayTeam"]))
selected_teams = st.sidebar.multiselect("Team (home or away)", all_teams, default=[])

filtered = df[df["Season"].isin(selected_seasons)]
if selected_teams:
    filtered = filtered[
        filtered["HomeTeam"].isin(selected_teams) | filtered["AwayTeam"].isin(selected_teams)
    ]

if filtered.empty:
    st.warning("No matches for the current filter selection.")
    st.stop()

# ---------- Overview / EDA ----------
st.header("Dataset Overview")

c1, c2, c3, c4 = st.columns(4)
c1.metric("Matches", f"{len(filtered):,}")
c2.metric("Seasons", filtered["Season"].nunique())
c3.metric("Teams", len(set(filtered["HomeTeam"]) | set(filtered["AwayTeam"])))
c4.metric("Avg goals / match", f"{filtered['TotalGoals'].mean():.2f}")

with st.expander("Preview raw data"):
    st.dataframe(filtered.head(50), use_container_width=True)

with st.expander("Column info & missing values"):
    info_df = pd.DataFrame(
        {
            "dtype": filtered.dtypes.astype(str),
            "missing": filtered.isna().sum(),
            "missing_%": (filtered.isna().mean() * 100).round(1),
        }
    )
    st.dataframe(info_df, use_container_width=True)

with st.expander("Summary statistics (numeric columns)"):
    st.dataframe(filtered.describe().T, use_container_width=True)

st.divider()

# ---------- Visualizations ----------
st.header("Visualizations")

tab1, tab2, tab3, tab4, tab5 = st.tabs(
    ["Results & Goals", "Team Performance", "Discipline", "Shots", "Trends over time"]
)

with tab1:
    col1, col2 = st.columns(2)

    with col1:
        result_counts = filtered["FullTimeResult"].map(
            {"H": "Home win", "D": "Draw", "A": "Away win"}
        ).value_counts()
        fig = px.pie(
            values=result_counts.values,
            names=result_counts.index,
            title="Full-time result distribution",
            hole=0.4,
        )
        st.plotly_chart(fig, use_container_width=True)

    with col2:
        fig = px.histogram(
            filtered,
            x="TotalGoals",
            nbins=filtered["TotalGoals"].max() + 1,
            title="Distribution of total goals per match",
            labels={"TotalGoals": "Total goals in match"},
        )
        st.plotly_chart(fig, use_container_width=True)

    goals_by_season = (
        filtered.groupby("Season")["TotalGoals"].mean().reset_index()
    )
    fig = px.bar(
        goals_by_season,
        x="Season",
        y="TotalGoals",
        title="Average goals per match by season",
        labels={"TotalGoals": "Avg total goals"},
    )
    st.plotly_chart(fig, use_container_width=True)

with tab2:
    home_goals = filtered.groupby("HomeTeam")["HomeGoals"].sum()
    away_goals = filtered.groupby("AwayTeam")["AwayGoals"].sum()
    goals_scored = (home_goals.add(away_goals, fill_value=0)).sort_values(ascending=False)

    top_n = st.slider("Show top N teams by goals scored", 5, min(30, len(goals_scored)), 15)
    goals_df = goals_scored.head(top_n).sort_values().reset_index()
    goals_df.columns = ["Team", "GoalsScored"]
    fig = px.bar(
        goals_df,
        x="GoalsScored",
        y="Team",
        orientation="h",
        labels={"GoalsScored": "Goals scored", "Team": "Team"},
        title=f"Top {top_n} teams by total goals scored (filtered seasons)",
    )
    st.plotly_chart(fig, use_container_width=True)

    home_wins = filtered[filtered["FullTimeResult"] == "H"].groupby("HomeTeam").size()
    away_wins = filtered[filtered["FullTimeResult"] == "A"].groupby("AwayTeam").size()
    home_played = filtered.groupby("HomeTeam").size()
    away_played = filtered.groupby("AwayTeam").size()
    wins = home_wins.add(away_wins, fill_value=0)
    played = home_played.add(away_played, fill_value=0)
    win_rate = (wins / played * 100).round(1).sort_values(ascending=False)

    top_n2 = st.slider("Show top N teams by win rate", 5, min(30, len(win_rate)), 15, key="winrate")
    win_df = win_rate.head(top_n2).reset_index()
    win_df.columns = ["Team", "WinRate"]
    fig = px.bar(
        win_df.sort_values("WinRate"),
        x="WinRate",
        y="Team",
        orientation="h",
        title=f"Top {top_n2} teams by win rate % (filtered seasons)",
        labels={"WinRate": "Win rate (%)"},
    )
    st.plotly_chart(fig, use_container_width=True)

with tab3:
    col1, col2 = st.columns(2)
    with col1:
        cards_by_season = filtered.groupby("Season")[
            ["HomeYellow", "AwayYellow"]
        ].sum()
        cards_by_season["TotalYellow"] = (
            cards_by_season["HomeYellow"] + cards_by_season["AwayYellow"]
        )
        fig = px.bar(
            cards_by_season.reset_index(),
            x="Season",
            y="TotalYellow",
            title="Total yellow cards per season",
        )
        st.plotly_chart(fig, use_container_width=True)

    with col2:
        reds_by_season = filtered.groupby("Season")[["HomeRed", "AwayRed"]].sum()
        reds_by_season["TotalRed"] = reds_by_season["HomeRed"] + reds_by_season["AwayRed"]
        fig = px.bar(
            reds_by_season.reset_index(),
            x="Season",
            y="TotalRed",
            title="Total red cards per season",
        )
        st.plotly_chart(fig, use_container_width=True)

    if "Referee" in filtered.columns:
        fouls = filtered.groupby("Referee")[["HomeFouls", "AwayFouls"]].sum()
        fouls["TotalFouls"] = fouls["HomeFouls"] + fouls["AwayFouls"]
        matches_reffed = filtered.groupby("Referee").size()
        fouls["MatchesReffed"] = matches_reffed
        fouls = fouls[fouls["MatchesReffed"] >= 10]
        fouls["FoulsPerMatch"] = (fouls["TotalFouls"] / fouls["MatchesReffed"]).round(2)
        fouls = fouls.sort_values("FoulsPerMatch", ascending=False).head(15)
        fig = px.bar(
            fouls.reset_index(),
            x="Referee",
            y="FoulsPerMatch",
            title="Fouls per match by referee (min. 10 matches, top 15)",
        )
        fig.update_xaxes(tickangle=45)
        st.plotly_chart(fig, use_container_width=True)

with tab4:
    fig = px.scatter(
        filtered,
        x="HomeShots",
        y="HomeGoals",
        color="Season",
        trendline="ols",
        title="Home shots vs. home goals",
        opacity=0.6,
    )
    st.plotly_chart(fig, use_container_width=True)

    filtered["HomeShotAccuracy"] = (
        filtered["HomeShotsOnTarget"] / filtered["HomeShots"]
    ).replace([float("inf")], None)
    fig = px.histogram(
        filtered,
        x="HomeShotAccuracy",
        nbins=30,
        title="Home shot accuracy distribution (shots on target / total shots)",
    )
    st.plotly_chart(fig, use_container_width=True)

    corr_cols = [
        "HomeGoals", "AwayGoals", "HomeShots", "AwayShots",
        "HomeShotsOnTarget", "AwayShotsOnTarget", "HomeCorners", "AwayCorners",
        "HomeFouls", "AwayFouls", "HomeYellow", "AwayYellow",
    ]
    corr_cols = [c for c in corr_cols if c in filtered.columns]
    corr = filtered[corr_cols].corr()
    fig = px.imshow(
        corr,
        text_auto=".2f",
        aspect="auto",
        title="Correlation heatmap of match stats",
        color_continuous_scale="RdBu_r",
        zmin=-1,
        zmax=1,
    )
    st.plotly_chart(fig, use_container_width=True)

with tab5:
    ts = filtered.set_index("Date").sort_index()
    monthly_goals = ts["TotalGoals"].resample("ME").mean().reset_index()
    fig = px.line(
        monthly_goals,
        x="Date",
        y="TotalGoals",
        title="Average total goals per match, by month",
        markers=True,
    )
    st.plotly_chart(fig, use_container_width=True)

    monthly_results = (
        ts.groupby([pd.Grouper(freq="ME"), "FullTimeResult"]).size().reset_index(name="Count")
    )
    monthly_results["FullTimeResult"] = monthly_results["FullTimeResult"].map(
        {"H": "Home win", "D": "Draw", "A": "Away win"}
    )
    fig = px.area(
        monthly_results,
        x="Date",
        y="Count",
        color="FullTimeResult",
        title="Match results over time (monthly)",
    )
    st.plotly_chart(fig, use_container_width=True)

st.divider()
st.caption("Data source: football-data.co.uk — free historical football results & odds data.")
