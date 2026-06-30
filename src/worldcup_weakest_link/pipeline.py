from __future__ import annotations

import math
from pathlib import Path
from typing import Iterable

import numpy as np
import pandas as pd

from . import schemas


PROJECT_ROOT = Path(__file__).resolve().parents[2]
RAW_DIR = PROJECT_ROOT / "data" / "raw"
REF_DIR = PROJECT_ROOT / "data" / "reference"
PROCESSED_DIR = PROJECT_ROOT / "data" / "processed"
OUTPUT_DIR = PROJECT_ROOT / "outputs"


def read_csv(path: Path, columns: list[str]) -> pd.DataFrame:
    if not path.exists():
        return pd.DataFrame(columns=columns)
    df = pd.read_csv(path)
    for column in columns:
        if column not in df.columns:
            df[column] = pd.NA
    return df[columns + [c for c in df.columns if c not in columns]]


def write_csv(df: pd.DataFrame, path: Path, columns: list[str] | None = None) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if columns is not None:
        for column in columns:
            if column not in df.columns:
                df[column] = pd.NA
        df = df[columns]
    df.to_csv(path, index=False)


def coerce_numeric(df: pd.DataFrame, columns: Iterable[str]) -> pd.DataFrame:
    df = df.copy()
    for column in columns:
        if column in df.columns:
            df[column] = pd.to_numeric(df[column], errors="coerce")
    return df


def normalize_bool(series: pd.Series) -> pd.Series:
    return series.astype(str).str.strip().str.lower().isin(["1", "true", "yes", "y"])


def validate_inputs(
    minutes: pd.DataFrame,
    values: pd.DataFrame,
    standings: pd.DataFrame,
    exchange: pd.DataFrame,
) -> list[dict[str, str]]:
    issues: list[dict[str, str]] = []

    def add(check: str, severity: str, message: str) -> None:
        issues.append({"check": check, "severity": severity, "message": message})

    for name, df in [
        ("player_minutes", minutes),
        ("player_market_values", values),
        ("group_standings", standings),
        ("exchange_rate", exchange),
    ]:
        if df.empty:
            add(name, "blocking", f"{name}.csv is empty or missing; analysis cannot be run.")

    if not standings.empty:
        team_counts = standings["team"].value_counts(dropna=False)
        duplicated = team_counts[team_counts != 1]
        if len(standings) != 48:
            add("team_count", "blocking", f"group_standings has {len(standings)} rows, expected 48.")
        if not duplicated.empty:
            add("unique_teams", "blocking", f"Teams not appearing exactly once: {duplicated.to_dict()}")
        if "matches_played" in standings:
            bad_matches = standings[pd.to_numeric(standings["matches_played"], errors="coerce") != 3]
            if not bad_matches.empty:
                add("matches_played", "review", f"{len(bad_matches)} teams do not show exactly 3 matches.")

    if not minutes.empty:
        minutes_num = pd.to_numeric(minutes["minutes"], errors="coerce")
        if (minutes_num <= 0).any():
            add("appeared_players", "review", "Some player-minute rows have zero or negative minutes.")
        dupes = minutes.duplicated(subset=["team", "player"], keep=False)
        if dupes.any():
            add("duplicate_player_country", "blocking", f"{int(dupes.sum())} duplicated team-player minute rows.")
        impossible = minutes_num > (3 * 120)
        if impossible.any():
            add("minutes_range", "review", f"{int(impossible.sum())} player rows exceed 360 minutes.")

    if not values.empty:
        missing_as_zero = (
            normalize_bool(values["missing_value_flag"])
            & (pd.to_numeric(values["market_value_original"], errors="coerce") == 0)
        )
        if missing_as_zero.any():
            add("missing_not_zero", "blocking", f"{int(missing_as_zero.sum())} missing market values are coded as zero.")
        currencies = set(values["currency"].dropna().astype(str).str.upper())
        if "USD" in currencies and "EUR" in currencies:
            add("mixed_currency", "review", "Market values contain both EUR and USD; confirm original currency per row.")
        missing_flags = normalize_bool(values["missing_value_flag"])
        missing_count = int(missing_flags.sum())
        if missing_count:
            add("missing_market_values", "blocking", f"{missing_count} market-value rows are flagged missing; value-based analysis is not complete.")
        sourced_values = values[~missing_flags]
        if not sourced_values.empty and (
            sourced_values["source_url"].isna().any()
            or (sourced_values["source_url"].astype(str).str.strip() == "").any()
        ):
            add("market_value_sources", "blocking", "Every non-missing market-value row must include a source_url.")

    if not exchange.empty:
        if len(exchange) != 1:
            add("exchange_rate_rows", "blocking", f"exchange_rate.csv must contain exactly one row; found {len(exchange)}.")
        rate = pd.to_numeric(exchange.get("eur_to_usd"), errors="coerce")
        if rate.isna().any() or (rate <= 0).any():
            add("exchange_rate_value", "blocking", "EUR-to-USD exchange rate must be a positive number.")

    return issues


def select_core_xi(minutes: pd.DataFrame, values: pd.DataFrame, exchange: pd.DataFrame) -> pd.DataFrame:
    minutes = coerce_numeric(minutes, ["minutes", "starts", "appearances"]).copy()
    values = coerce_numeric(values, ["age", "market_value_original"]).copy()
    if minutes.empty:
        return pd.DataFrame(columns=schemas.CORE_XI_COLUMNS)

    minutes = minutes.sort_values(
        ["team", "minutes", "starts", "appearances", "player"],
        ascending=[True, False, False, False, True],
        kind="mergesort",
    )
    minutes["core_xi_rank_by_minutes"] = minutes.groupby("team").cumcount() + 1

    def tie_flags(group: pd.DataFrame) -> pd.Series:
        flags = pd.Series(False, index=group.index)
        if len(group) >= 12:
            border = group.iloc[[10, 11]][["minutes", "starts", "appearances"]]
            if border.iloc[0].equals(border.iloc[1]):
                flags.loc[group.index[10:12]] = True
        return flags

    minutes["tie_flag"] = minutes.groupby("team", group_keys=False).apply(tie_flags, include_groups=False)
    core = minutes[minutes["core_xi_rank_by_minutes"] <= 11].copy()
    core = core.rename(columns={"position": "position_minutes_source"})

    merged = core.merge(
        values,
        on=["team", "player"],
        how="left",
        suffixes=("", "_market"),
    )
    if "position" not in merged.columns:
        merged["position"] = pd.NA

    rate = np.nan
    if not exchange.empty:
        rate = pd.to_numeric(exchange["eur_to_usd"], errors="coerce").iloc[0]

    currency = merged["currency"].astype(str).str.upper().str.strip()
    original = pd.to_numeric(merged["market_value_original"], errors="coerce")
    merged["market_value_usd"] = np.where(
        currency.eq("EUR"),
        original * rate,
        np.where(currency.eq("USD"), original, np.nan),
    )
    merged["missing_value_flag"] = normalize_bool(merged["missing_value_flag"]) | merged["market_value_usd"].isna()
    merged["market_value_source_url"] = merged["source_url_market"] if "source_url_market" in merged else pd.NA
    merged["market_value_retrieval_date"] = merged["retrieval_date_market"] if "retrieval_date_market" in merged else pd.NA

    merged["player_value_rank_within_team"] = (
        merged.groupby("team")["market_value_usd"]
        .rank(method="first", ascending=False, na_option="keep")
        .astype("Int64")
    )
    merged["top_three_flag"] = merged["market_value_usd"].notna() & merged["player_value_rank_within_team"].le(3)
    bottom_rank = (
        merged.groupby("team")["market_value_usd"]
        .rank(method="first", ascending=True, na_option="keep")
    )
    merged["bottom_three_flag"] = merged["market_value_usd"].notna() & bottom_rank.le(3)
    return merged


def safe_divide(numerator: float, denominator: float) -> float:
    if denominator is None or pd.isna(denominator) or denominator == 0:
        return np.nan
    return numerator / denominator


def calculate_team_metrics(core: pd.DataFrame) -> pd.DataFrame:
    rows = []
    if core.empty:
        return pd.DataFrame(columns=schemas.TEAM_METRIC_COLUMNS)
    for team, group in core.groupby("team", dropna=False):
        values = pd.to_numeric(group["market_value_usd"], errors="coerce").dropna().sort_values(ascending=False)
        total = float(values.sum()) if not values.empty else np.nan
        avg = float(values.mean()) if not values.empty else np.nan
        median = float(values.median()) if not values.empty else np.nan
        top3 = values.head(3)
        bottom3 = values.tail(3)
        top_1 = float(values.iloc[0]) if len(values) else np.nan
        bottom_1 = float(values.iloc[-1]) if len(values) else np.nan
        top3_avg = float(top3.mean()) if len(top3) == 3 else np.nan
        bottom3_avg = float(bottom3.mean()) if len(bottom3) == 3 else np.nan
        bottom3_total = float(bottom3.sum()) if len(bottom3) == 3 else np.nan
        std = float(values.std(ddof=0)) if len(values) else np.nan
        rows.append(
            {
                "team": team,
                "core_xi_players": int(len(group)),
                "core_xi_missing_values": int(group["market_value_usd"].isna().sum()),
                "core_xi_total_value_usd": total,
                "core_xi_average_value_usd": avg,
                "core_xi_median_value_usd": median,
                "top_1_value_usd": top_1,
                "top_3_average_value_usd": top3_avg,
                "bottom_1_value_usd": bottom_1,
                "bottom_3_average_value_usd": bottom3_avg,
                "bottom_3_total_value_usd": bottom3_total,
                "highest_to_lowest_ratio": safe_divide(top_1, bottom_1),
                "top_3_share_of_xi_value": safe_divide(float(top3.sum()), total),
                "bottom_3_share_of_xi_value": safe_divide(bottom3_total, total),
                "value_standard_deviation": std,
                "value_coefficient_of_variation": safe_divide(std, avg),
                "lineup_imbalance": safe_divide(top3_avg, bottom3_avg),
            }
        )
    return pd.DataFrame(rows)


def build_analysis_dataset(metrics: pd.DataFrame, standings: pd.DataFrame) -> pd.DataFrame:
    if metrics.empty:
        return pd.DataFrame(columns=schemas.ANALYSIS_COLUMNS)
    standings = coerce_numeric(
        standings,
        [
            "matches_played",
            "wins",
            "draws",
            "losses",
            "goals_for",
            "goals_against",
            "goal_difference",
            "points",
            "group_position",
        ],
    )
    standings["advanced_flag"] = normalize_bool(standings["advanced_flag"])
    df = metrics.merge(standings, on="team", how="left")
    df["points_per_match"] = df["points"] / df["matches_played"]
    df["goal_difference_per_match"] = df["goal_difference"] / df["matches_played"]
    return df


def calculate_correlations(analysis: pd.DataFrame) -> pd.DataFrame:
    predictors = [
        "core_xi_total_value_usd",
        "core_xi_average_value_usd",
        "top_3_average_value_usd",
        "bottom_3_average_value_usd",
        "core_xi_median_value_usd",
        "lineup_imbalance",
    ]
    outcomes = ["points", "goal_difference", "group_position"]
    rows = []
    try:
        from scipy import stats
    except Exception:
        stats = None

    def spearman_corr(left: pd.Series, right: pd.Series) -> float:
        if stats:
            return stats.spearmanr(left, right).statistic
        return left.rank(method="average").corr(right.rank(method="average"), method="pearson")

    for outcome in outcomes:
        for predictor in predictors:
            subset = analysis[[outcome, predictor]].dropna()
            if len(subset) < 3:
                for method in ["pearson", "spearman"]:
                    rows.append(
                        {
                            "outcome": outcome,
                            "predictor": predictor,
                            "method": method,
                            "n": len(subset),
                            "correlation": np.nan,
                            "p_value": np.nan,
                            "notes": "Fewer than 3 complete observations.",
                        }
                    )
                continue
            pearson = subset[outcome].corr(subset[predictor], method="pearson")
            spearman = spearman_corr(subset[outcome], subset[predictor])
            pearson_p = stats.pearsonr(subset[predictor], subset[outcome]).pvalue if stats else np.nan
            spearman_p = stats.spearmanr(subset[predictor], subset[outcome]).pvalue if stats else np.nan
            rows.extend(
                [
                    {
                        "outcome": outcome,
                        "predictor": predictor,
                        "method": "pearson",
                        "n": len(subset),
                        "correlation": pearson,
                        "p_value": pearson_p,
                        "notes": "Group position is ordinal; negative correlation means stronger predictor values align with better positions.",
                    },
                    {
                        "outcome": outcome,
                        "predictor": predictor,
                        "method": "spearman",
                        "n": len(subset),
                        "correlation": spearman,
                        "p_value": spearman_p,
                        "notes": "Spearman uses rank order.",
                    },
                ]
            )
    return pd.DataFrame(rows)


def log_value_columns(df: pd.DataFrame, columns: list[str]) -> pd.DataFrame:
    df = df.copy()
    for column in columns:
        df[f"log_{column}"] = np.log(pd.to_numeric(df[column], errors="coerce"))
        df.loc[~np.isfinite(df[f"log_{column}"]), f"log_{column}"] = np.nan
    return df


def run_logistic_regressions(analysis: pd.DataFrame) -> pd.DataFrame:
    models = {
        "total_xi_value_only": ["core_xi_total_value_usd"],
        "top_three_average_only": ["top_3_average_value_usd"],
        "bottom_three_average_only": ["bottom_3_average_value_usd"],
        "total_plus_bottom_three": ["core_xi_total_value_usd", "bottom_3_average_value_usd"],
        "top_three_plus_bottom_three": ["top_3_average_value_usd", "bottom_3_average_value_usd"],
        "average_value_plus_imbalance": ["core_xi_average_value_usd", "lineup_imbalance"],
    }
    value_predictors = sorted({p for ps in models.values() for p in ps if p != "lineup_imbalance"})
    df = log_value_columns(analysis, value_predictors)
    try:
        import statsmodels.api as sm
        from sklearn.metrics import accuracy_score, roc_auc_score
        from sklearn.model_selection import StratifiedKFold, cross_val_predict
        from sklearn.linear_model import LogisticRegression
    except Exception as exc:
        return pd.DataFrame(
            [
                {
                    "model": "all",
                    "predictors": "",
                    "n": len(analysis),
                    "term": "",
                    "coefficient": np.nan,
                    "odds_ratio": np.nan,
                    "p_value": np.nan,
                    "mcfadden_pseudo_r2": np.nan,
                    "aic": np.nan,
                    "roc_auc": np.nan,
                    "classification_accuracy_cv": np.nan,
                    "notes": f"Regression dependencies unavailable: {exc}",
                }
            ]
        )

    rows = []
    for model_name, predictors in models.items():
        design_cols = [f"log_{p}" if p != "lineup_imbalance" else p for p in predictors]
        subset = df[["advanced_flag"] + design_cols].dropna()
        if len(subset) < 20 or subset["advanced_flag"].nunique() < 2:
            rows.append(
                {
                    "model": model_name,
                    "predictors": ", ".join(predictors),
                    "n": len(subset),
                    "term": "",
                    "coefficient": np.nan,
                    "odds_ratio": np.nan,
                    "p_value": np.nan,
                    "mcfadden_pseudo_r2": np.nan,
                    "aic": np.nan,
                    "roc_auc": np.nan,
                    "classification_accuracy_cv": np.nan,
                    "notes": "Insufficient complete observations or outcome variation.",
                }
            )
            continue
        y = subset["advanced_flag"].astype(int)
        x = sm.add_constant(subset[design_cols], has_constant="add")
        try:
            result = sm.Logit(y, x).fit(disp=False)
            pred = result.predict(x)
            auc = roc_auc_score(y, pred)
            acc = np.nan
            if y.value_counts().min() >= 3:
                cv = StratifiedKFold(n_splits=3, shuffle=True, random_state=2026)
                clf = LogisticRegression(max_iter=1000)
                classes = cross_val_predict(clf, subset[design_cols], y, cv=cv)
                acc = accuracy_score(y, classes)
            null_llf = result.llnull
            pseudo_r2 = 1 - (result.llf / null_llf) if null_llf else np.nan
            for term in result.params.index:
                rows.append(
                    {
                        "model": model_name,
                        "predictors": ", ".join(predictors),
                        "n": len(subset),
                        "term": term,
                        "coefficient": result.params[term],
                        "odds_ratio": math.exp(result.params[term]),
                        "p_value": result.pvalues[term],
                        "mcfadden_pseudo_r2": pseudo_r2,
                        "aic": result.aic,
                        "roc_auc": auc,
                        "classification_accuracy_cv": acc,
                        "notes": "Log-transformed USD values used except lineup_imbalance.",
                    }
                )
        except Exception as exc:
            rows.append(
                {
                    "model": model_name,
                    "predictors": ", ".join(predictors),
                    "n": len(subset),
                    "term": "",
                    "coefficient": np.nan,
                    "odds_ratio": np.nan,
                    "p_value": np.nan,
                    "mcfadden_pseudo_r2": np.nan,
                    "aic": np.nan,
                    "roc_auc": np.nan,
                    "classification_accuracy_cv": np.nan,
                    "notes": f"Model failed: {exc}",
                }
            )
    return pd.DataFrame(rows)


def build_rankings(analysis: pd.DataFrame) -> pd.DataFrame:
    if analysis.empty:
        return pd.DataFrame(columns=schemas.RANKING_COLUMNS)
    specs = [
        ("highest_bottom_three_value", "bottom_3_average_value_usd", False),
        ("lowest_bottom_three_value", "bottom_3_average_value_usd", True),
        ("most_balanced_core_xi", "lineup_imbalance", True),
        ("most_top_heavy_core_xi", "lineup_imbalance", False),
    ]
    rows = []
    for ranking, column, ascending in specs:
        ranked = analysis.dropna(subset=[column]).sort_values(column, ascending=ascending).head(10)
        for idx, (_, row) in enumerate(ranked.iterrows(), start=1):
            rows.append(
                {
                    "ranking": ranking,
                    "rank": idx,
                    "team": row["team"],
                    "value": row[column],
                    "points": row.get("points"),
                    "goal_difference": row.get("goal_difference"),
                    "advanced_flag": row.get("advanced_flag"),
                    "notes": column,
                }
            )
    # Simple value-based expected points model for over/underperformance.
    complete = analysis[["team", "points", "goal_difference", "advanced_flag", "core_xi_total_value_usd"]].dropna()
    if len(complete) >= 10:
        x = np.log(complete["core_xi_total_value_usd"].astype(float))
        y = complete["points"].astype(float)
        slope, intercept = np.polyfit(x, y, 1)
        complete = complete.copy()
        complete["value"] = y - (intercept + slope * x)
        for ranking, ascending in [("biggest_overperformers_relative_to_value", False), ("biggest_underperformers_relative_to_value", True)]:
            for idx, (_, row) in enumerate(complete.sort_values("value", ascending=ascending).head(10).iterrows(), start=1):
                rows.append(
                    {
                        "ranking": ranking,
                        "rank": idx,
                        "team": row["team"],
                        "value": row["value"],
                        "points": row["points"],
                        "goal_difference": row["goal_difference"],
                        "advanced_flag": row["advanced_flag"],
                        "notes": "Actual points minus expected points from log total XI value.",
                    }
                )
    return pd.DataFrame(rows)


def build_tableau(core: pd.DataFrame, analysis: pd.DataFrame) -> pd.DataFrame:
    if core.empty:
        return pd.DataFrame(columns=schemas.TABLEAU_COLUMNS)
    team_cols = [
        "team",
        "group",
        "core_xi_total_value_usd",
        "core_xi_average_value_usd",
        "bottom_3_average_value_usd",
        "top_3_average_value_usd",
        "lineup_imbalance",
        "points",
        "goal_difference",
        "group_position",
        "advanced_flag",
        "qualification_type",
    ]
    tableau = core.merge(analysis[team_cols], on="team", how="left")
    tableau = tableau.rename(
        columns={
            "position_minutes_source": "position",
            "core_xi_total_value_usd": "team_total_xi_value",
            "core_xi_average_value_usd": "team_average_xi_value",
        }
    )
    tableau["core_xi_total_value_usd"] = tableau["team_total_xi_value"]
    tableau["core_xi_average_value_usd"] = tableau["team_average_xi_value"]
    return tableau


def data_quality_report(issues: list[dict[str, str]], core: pd.DataFrame, metrics: pd.DataFrame) -> pd.DataFrame:
    rows = issues.copy()
    if not core.empty:
        counts = core.groupby("team").size()
        bad_counts = counts[counts != 11]
        if not bad_counts.empty:
            rows.append(
                {
                    "check": "core_xi_count",
                    "severity": "blocking",
                    "message": f"Teams without exactly 11 Core XI players: {bad_counts.to_dict()}",
                }
            )
        if core["tie_flag"].fillna(False).any():
            rows.append(
                {
                    "check": "core_xi_ties",
                    "severity": "review",
                    "message": "At least one team has an unresolved tie at the Core XI selection boundary.",
                }
            )
    if not metrics.empty and not core.empty:
        summed = core.groupby("team")["market_value_usd"].sum(min_count=1)
        joined = metrics.set_index("team")["core_xi_total_value_usd"].to_frame("metric_total").join(summed.rename("player_total"))
        mismatch = joined[~np.isclose(joined["metric_total"], joined["player_total"], equal_nan=True)]
        if not mismatch.empty:
            rows.append(
                {
                    "check": "team_totals_match_players",
                    "severity": "blocking",
                    "message": f"{len(mismatch)} team-level totals do not equal player-level sums.",
                }
            )
    if not rows:
        rows.append({"check": "all_checks", "severity": "ok", "message": "No unresolved data-quality issues detected."})
    return pd.DataFrame(rows)


def main() -> None:
    minutes = read_csv(RAW_DIR / "player_minutes.csv", schemas.PLAYER_MINUTES_COLUMNS)
    values = read_csv(RAW_DIR / "player_market_values.csv", schemas.PLAYER_MARKET_VALUE_COLUMNS)
    standings = read_csv(RAW_DIR / "group_standings.csv", schemas.GROUP_STANDINGS_COLUMNS)
    exchange = read_csv(REF_DIR / "exchange_rate.csv", schemas.EXCHANGE_RATE_COLUMNS)

    issues = validate_inputs(minutes, values, standings, exchange)
    core = select_core_xi(minutes, values, exchange)
    metrics = calculate_team_metrics(core)
    analysis = build_analysis_dataset(metrics, standings)
    correlations = calculate_correlations(analysis)
    regressions = run_logistic_regressions(analysis)
    rankings = build_rankings(analysis)
    tableau = build_tableau(core, analysis)
    quality = data_quality_report(issues, core, metrics)

    write_csv(core, PROCESSED_DIR / "core_xi_players.csv", schemas.CORE_XI_COLUMNS)
    write_csv(metrics, PROCESSED_DIR / "team_metrics.csv", schemas.TEAM_METRIC_COLUMNS)
    write_csv(analysis, PROCESSED_DIR / "analysis_dataset.csv", schemas.ANALYSIS_COLUMNS)
    write_csv(correlations, OUTPUT_DIR / "correlation_results.csv", schemas.CORRELATION_COLUMNS)
    write_csv(regressions, OUTPUT_DIR / "regression_results.csv", schemas.REGRESSION_COLUMNS)
    write_csv(rankings, OUTPUT_DIR / "team_rankings.csv", schemas.RANKING_COLUMNS)
    write_csv(quality, OUTPUT_DIR / "data_quality_report.csv")
    write_csv(tableau, OUTPUT_DIR / "tableau_world_cup_weakest_link.csv", schemas.TABLEAU_COLUMNS)


if __name__ == "__main__":
    main()
