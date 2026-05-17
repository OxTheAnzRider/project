"""
train.py — Generate synthetic dataset and train both AI models.

Run once before starting the microservice:
    python app/train.py

Outputs saved to models/:
    competency_model.joblib   — Random Forest classifier (Model A)
    anomaly_model.joblib      — Isolation Forest detector (Model B)
    scaler.joblib             — Min-max scaler fitted on training data
    feature_names.json        — Ordered list of feature names
"""

import json
import os
import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestClassifier, IsolationForest
from sklearn.model_selection import train_test_split, GridSearchCV, StratifiedKFold
from sklearn.preprocessing import MinMaxScaler
from sklearn.metrics import (
    classification_report, confusion_matrix,
    roc_auc_score, f1_score
)
import joblib

RANDOM_STATE = 42
MODELS_DIR   = os.path.join(os.path.dirname(__file__), "..", "models")
os.makedirs(MODELS_DIR, exist_ok=True)

PROGRAMMES = [
    "electrical_installation",
    "welding_fabrication",
    "garment_construction",
    "building_technology",
    "ict",
]

# ── 1. Synthetic Dataset Generation ────────────────────────────────────────

def generate_dataset(n: int = 2847, seed: int = RANDOM_STATE) -> pd.DataFrame:
    """
    Generate a realistic synthetic assessment dataset.
    Feature schema matches FR-03 specification from Chapter Three.
    """
    rng = np.random.default_rng(seed)
    rows = []

    per_programme = n // len(PROGRAMMES)

    for prog in PROGRAMMES:
        for _ in range(per_programme):
            # Ground truth: ~78% pass rate
            true_pass = rng.random() < 0.78

            # --- Rubric scores (1-5 scale) ---
            if true_pass:
                rubric = rng.integers(3, 6, size=5).astype(float)   # 3-5
            else:
                rubric = rng.integers(1, 4, size=5).astype(float)   # 1-3
            # small random noise
            rubric = np.clip(rubric + rng.uniform(-0.3, 0.3, 5), 1, 5)

            # --- Knowledge sub-tests (0-1 normalised) ---
            if true_pass:
                knowledge = rng.uniform(0.55, 1.0, size=3)
            else:
                knowledge = rng.uniform(0.0, 0.60, size=3)

            # --- Submission metadata ---
            attempts         = int(rng.integers(1, 4))
            days_before_end  = rng.uniform(1, 30)
            upload_lag_hours = rng.uniform(0.1, 48)
            has_attestation  = float(rng.random() < 0.85)

            # --- Anomaly injection (~3.1% of records) ---
            is_anomaly = 0
            if rng.random() < 0.031:
                is_anomaly = 1
                # fabricated: max rubric but low knowledge
                rubric    = np.array([5.0, 5.0, 5.0, 5.0, 5.0])
                knowledge = rng.uniform(0.0, 0.40, size=3)
                days_before_end = rng.uniform(0, 0.01)  # backdated

            rows.append({
                # Rubric
                "rubric_technical":    round(rubric[0], 2),
                "rubric_practical":    round(rubric[1], 2),
                "rubric_safety":       round(rubric[2], 2),
                "rubric_problemsolve": round(rubric[3], 2),
                "rubric_professional": round(rubric[4], 2),
                # Knowledge
                "know_foundations":   round(knowledge[0], 4),
                "know_regulatory":    round(knowledge[1], 4),
                "know_applied":       round(knowledge[2], 4),
                # Metadata
                "attempts":           attempts,
                "days_before_end":    round(days_before_end, 2),
                "upload_lag_hours":   round(upload_lag_hours, 2),
                "has_attestation":    has_attestation,
                # Programme (will be one-hot encoded)
                "programme":          prog,
                # Labels
                "outcome":            int(true_pass),
                "is_anomaly":         is_anomaly,
            })

    df = pd.DataFrame(rows).sample(frac=1, random_state=seed).reset_index(drop=True)
    print(f"Dataset: {len(df)} records | PASS rate: {df['outcome'].mean():.1%} | Anomalies: {df['is_anomaly'].sum()}")
    return df


# ── 2. Preprocessing ────────────────────────────────────────────────────────

def preprocess(df: pd.DataFrame):
    # One-hot encode programme
    prog_dummies = pd.get_dummies(df["programme"], prefix="prog")
    numeric_cols = [
        "rubric_technical", "rubric_practical", "rubric_safety",
        "rubric_problemsolve", "rubric_professional",
        "know_foundations", "know_regulatory", "know_applied",
        "attempts", "days_before_end", "upload_lag_hours", "has_attestation",
    ]
    X = pd.concat([df[numeric_cols], prog_dummies], axis=1)
    y_competency = df["outcome"].values
    y_anomaly    = df["is_anomaly"].values

    feature_names = list(X.columns)
    return X, y_competency, y_anomaly, feature_names


# ── 3. Train Model A — Random Forest competency classifier ─────────────────

def train_competency_model(X_train, y_train):
    print("\n── Training Model A: Random Forest Competency Classifier ──")

    param_grid = {
        "n_estimators":     [200, 300],
        "max_depth":        [None, 20],
        "min_samples_split":[2, 5],
        "min_samples_leaf": [1, 2],
        "max_features":     ["sqrt"],
        "class_weight":     ["balanced"],
    }

    cv = StratifiedKFold(n_splits=5, shuffle=True, random_state=RANDOM_STATE)
    grid = GridSearchCV(
        RandomForestClassifier(random_state=RANDOM_STATE),
        param_grid,
        scoring="f1_macro",
        cv=cv,
        n_jobs=-1,
        verbose=1,
    )
    grid.fit(X_train, y_train)

    print(f"Best params:   {grid.best_params_}")
    print(f"CV F1-macro:   {grid.best_score_:.4f}")
    return grid.best_estimator_


# ── 4. Train Model B — Isolation Forest anomaly detector ──────────────────

def train_anomaly_model(X_train):
    print("\n── Training Model B: Isolation Forest Anomaly Detector ──")
    model = IsolationForest(
        n_estimators=200,
        contamination=0.05,    # slightly above observed 3.1%
        random_state=RANDOM_STATE,
        n_jobs=-1,
    )
    model.fit(X_train)
    print("Isolation Forest trained.")
    return model


# ── 5. Evaluate ─────────────────────────────────────────────────────────────

def evaluate(clf, iso, X_test, y_test, y_anomaly_test):
    print("\n── Model A Evaluation (held-out test set) ──")
    y_pred = clf.predict(X_test)
    print(classification_report(y_test, y_pred, target_names=["FAIL", "PASS"]))
    print("Confusion matrix:\n", confusion_matrix(y_test, y_pred))

    print("\n── Model B Evaluation ──")
    # IsolationForest: -1 = anomaly, 1 = normal
    iso_pred  = iso.predict(X_test)          # -1 or 1
    iso_label = (iso_pred == -1).astype(int) # 1 = flagged anomaly
    iso_score = -iso.score_samples(X_test)   # higher = more anomalous

    if y_anomaly_test.sum() > 0:
        auc = roc_auc_score(y_anomaly_test, iso_score)
        print(f"ROC-AUC:  {auc:.4f}")
        tp = ((iso_label == 1) & (y_anomaly_test == 1)).sum()
        fp = ((iso_label == 1) & (y_anomaly_test == 0)).sum()
        fn = ((iso_label == 0) & (y_anomaly_test == 1)).sum()
        precision = tp / (tp + fp + 1e-9)
        recall    = tp / (tp + fn + 1e-9)
        print(f"Precision: {precision:.4f}  Recall: {recall:.4f}")
        fpr = fp / (y_anomaly_test == 0).sum()
        print(f"FPR (normal flagged as anomaly): {fpr:.2%}")


# ── 6. Main ─────────────────────────────────────────────────────────────────

def main():
    print("=" * 60)
    print("  SkillCert AI — Model Training Pipeline")
    print("=" * 60)

    df = generate_dataset()
    X, y_comp, y_anom, feature_names = preprocess(df)

    # Scale
    scaler = MinMaxScaler()
    X_scaled = pd.DataFrame(
        scaler.fit_transform(X),
        columns=feature_names
    )

    # Stratified split
    X_train, X_test, y_train, y_test, ya_train, ya_test = train_test_split(
        X_scaled, y_comp, y_anom,
        test_size=0.20, stratify=y_comp, random_state=RANDOM_STATE
    )
    print(f"Train: {len(X_train)} | Test: {len(X_test)}")

    # Train
    clf = train_competency_model(X_train, y_train)
    iso = train_anomaly_model(X_train)

    # Evaluate
    evaluate(clf, iso, X_test, y_test, ya_test)

    # Save artefacts
    joblib.dump(clf,          os.path.join(MODELS_DIR, "competency_model.joblib"))
    joblib.dump(iso,          os.path.join(MODELS_DIR, "anomaly_model.joblib"))
    joblib.dump(scaler,       os.path.join(MODELS_DIR, "scaler.joblib"))
    with open(os.path.join(MODELS_DIR, "feature_names.json"), "w") as f:
        json.dump(feature_names, f, indent=2)

    print(f"\nModels saved to {MODELS_DIR}/")
    print("Training complete. Start the service with: uvicorn app.main:app --port 8001")


if __name__ == "__main__":
    main()