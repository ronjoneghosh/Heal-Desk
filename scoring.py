import pandas as pd

# --------------------------
# NORMALIZATION
# --------------------------
def normalize(series):
    return pd.qcut(series.rank(method='first'), 10, labels=False) + 1


# --------------------------
# USAGE PILLAR
# --------------------------
def calculate_usage_score(df):
    usage_raw = (
        df['logins_per_week'] * 0.3 +
        df['feature_usage_percent'] * 0.3 +
        df['interactions'] * 0.4
    )

    df['usage_score_1_10'] = normalize(usage_raw)
    return df


# --------------------------
# SUPPORT PILLAR
# --------------------------
def calculate_support_score(df):
    support_raw = (
        df['tickets_open'] * 0.6 +
        df['response_time'] * 0.4
    )

    df['support_score_1_10'] = 10 - normalize(support_raw)
    return df


# --------------------------
# FINAL HEALTH SCORE
# --------------------------
def calculate_chs(df):
    df['chs'] = (
        df['usage_score_1_10'] * 0.6 +
        df['support_score_1_10'] * 0.4
    )
    return df