import pandas as pd

# --------------------------
# NORMALIZATION (SAFE)
# --------------------------
def normalize(series):
    # Handle small datasets safely
    if len(series.dropna()) < 10:
        return pd.Series([5]*len(series), index=series.index)

    return pd.qcut(series.rank(method='first'), 10, labels=False) + 1


# --------------------------
# 🟦 USAGE SCORE (DYNAMIC)
# --------------------------
def calculate_usage_score(df):

    def row_score(row):
        components = []
        weights = []

        if 'usage_score_1_10' in row and not pd.isna(row['usage_score_1_10']):
            components.append(row['usage_score_1_10'] * 1.0)
            weights.append(1.0)

        # OPTIONAL FUTURE SIGNALS
        if 'feature_usage_score_1_10' in row and not pd.isna(row['feature_usage_score_1_10']):
            components.append(row['feature_usage_score_1_10'] * 0.5)
            weights.append(0.5)

        if 'engagement_score_1_10' in row and not pd.isna(row['engagement_score_1_10']):
            components.append(row['engagement_score_1_10'] * 0.5)
            weights.append(0.5)

        # ✅ NEW: RAW DATA SUPPORT (no breaking change)
        if 'logins' in row and not pd.isna(row['logins']):
            components.append((row['logins'] / 100) * 0.3)
            weights.append(0.3)

        if 'posts_created' in row and not pd.isna(row['posts_created']):
            components.append((row['posts_created'] / 50) * 0.3)
            weights.append(0.3)

        if len(weights) == 0:
            return None

        return sum(components) / sum(weights)

    df['usage_score_1_10'] = df.apply(row_score, axis=1)

    return df


# --------------------------
# 🟨 SUPPORT SCORE (DYNAMIC)
# --------------------------
def calculate_support_score(df):

    def row_score(row):
        components = []
        weights = []

        if 'support_score_1_10' in row and not pd.isna(row['support_score_1_10']):
            components.append(row['support_score_1_10'] * 1.0)
            weights.append(1.0)

        # FUTURE SUPPORT SIGNALS
        if 'ticket_volume' in row and not pd.isna(row['ticket_volume']):
            components.append((10 - row['ticket_volume']) * 0.5)
            weights.append(0.5)

        if 'escalations' in row and not pd.isna(row['escalations']):
            components.append((10 - row['escalations']) * 0.5)
            weights.append(0.5)

        # ✅ NEW: RAW SUPPORT SIGNAL
        if 'tickets' in row and not pd.isna(row['tickets']):
            components.append((10 - row['tickets']) * 0.3)
            weights.append(0.3)

        if len(weights) == 0:
            return None

        return sum(components) / sum(weights)

    df['support_score_1_10'] = df.apply(row_score, axis=1)

    return df


# --------------------------
# 🟪 CLIENT SUCCESS SCORE (NEW — ADDED ONLY)
# --------------------------
def calculate_cs_score(df):

    df['cs_score_1_10'] = (
        df.get('nps_score_0_10', 5) * 0.4 +
        df.get('csat_score_0_10', 5) * 0.3 +
        df.get('csm_sentiment_score_0_10', 5) * 0.3
    )

    return df


# --------------------------
# 🔥 FINAL CHS (DYNAMIC)
# --------------------------
def calculate_chs(df):

    def row_score(row):
        components = []
        weights = []

        if not pd.isna(row.get('usage_score_1_10')):
            components.append(row['usage_score_1_10'] * 0.35)
            weights.append(0.35)

        if not pd.isna(row.get('support_score_1_10')):
            components.append(row['support_score_1_10'] * 0.25)
            weights.append(0.25)

        if not pd.isna(row.get('engagement_score_1_10')):
            components.append(row['engagement_score_1_10'] * 0.2)
            weights.append(0.2)

        if not pd.isna(row.get('sentiment_score_1_10')):
            components.append(row['sentiment_score_1_10'] * 0.2)
            weights.append(0.2)

        # ✅ OPTIONAL FUTURE (does NOT break anything)
        if not pd.isna(row.get('cs_score_1_10')):
            components.append(row['cs_score_1_10'] * 0.1)
            weights.append(0.1)

        if len(weights) == 0:
            return None

        return sum(components) / sum(weights)

    df['chs'] = df.apply(row_score, axis=1)

    return df