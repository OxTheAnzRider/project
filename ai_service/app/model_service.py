"""Optional competency/anomaly model loading with strict feature compatibility."""

from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Any

log = logging.getLogger("ai.model_service")
MODELS_DIR = Path(__file__).resolve().parents[1] / "models"


class ModelService:
    def __init__(self):
        self.competency_model = None
        self.anomaly_model = None
        self.scaler = None
        self.feature_names: list[str] = []
        self._load()

    def _load(self) -> None:
        try:
            import joblib
        except Exception as exc:
            log.warning("joblib unavailable; model checks disabled: %s", exc)
            return

        required = {
            "competency": MODELS_DIR / "competency_model.joblib",
            "anomaly": MODELS_DIR / "anomaly_model.joblib",
            "scaler": MODELS_DIR / "scaler.joblib",
            "features": MODELS_DIR / "feature_names.json",
        }
        if not all(path.exists() for path in required.values()):
            log.warning("Model artifacts missing; competency/anomaly checks disabled")
            return
        try:
            self.competency_model = joblib.load(required["competency"])
            self.anomaly_model = joblib.load(required["anomaly"])
            self.scaler = joblib.load(required["scaler"])
            self.feature_names = json.loads(required["features"].read_text())
            log.info("Competency/anomaly models loaded")
        except Exception as exc:
            log.warning("Model loading failed; checks disabled: %s", exc)
            self.competency_model = None
            self.anomaly_model = None
            self.scaler = None
            self.feature_names = []

    def evaluate(self, features: dict[str, Any]) -> dict[str, Any]:
        missing = [name for name in self.feature_names if name not in features]
        available = bool(self.competency_model and self.anomaly_model and self.scaler and self.feature_names)
        if not available:
            return {
                "competency_prediction": None,
                "competency_model_used": False,
                "anomaly_detected": False,
                "anomaly_model_used": False,
                "model_reason": "model_artifacts_unavailable",
            }
        if missing:
            log.warning("Model feature mismatch; missing fields: %s", missing)
            return {
                "competency_prediction": None,
                "competency_model_used": False,
                "anomaly_detected": False,
                "anomaly_model_used": False,
                "model_reason": "feature_schema_mismatch",
            }
        try:
            import pandas as pd

            row = pd.DataFrame([[features[name] for name in self.feature_names]], columns=self.feature_names)
            scaled = self.scaler.transform(row)
            competency = bool(int(self.competency_model.predict(scaled)[0]) == 1)
            anomaly = bool(int(self.anomaly_model.predict(scaled)[0]) == -1)
            return {
                "competency_prediction": competency,
                "competency_model_used": True,
                "anomaly_detected": anomaly,
                "anomaly_model_used": True,
                "model_reason": "ok",
            }
        except Exception as exc:
            log.warning("Model prediction failed; checks skipped: %s", exc)
            return {
                "competency_prediction": None,
                "competency_model_used": False,
                "anomaly_detected": False,
                "anomaly_model_used": False,
                "model_reason": "prediction_failed",
            }


model_service = ModelService()
