"""Feature-logistic ML classifier (bundled + optional sklearn).

Status: IMPLEMENTED — never overrides verified identity.
Scores are model decision values / probabilities, not marketing claims.
"""

from __future__ import annotations

import json
import math
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from botscope.classify.result import (
    MODEL_VERSION,
    RULESET_VERSION,
    ClassificationResult,
    EvidenceItem,
)
from botscope.classify.taxonomy import BotCategory
from botscope.normalize.event import NormalizedEvent

# Bundled multiclass logistic over hand-crafted features, fit on labeled_mini
# (+ transparent priors). Coefficients are deterministic and inspected in tests.
FEATURE_ORDER = [
    "ua_len",
    "ua_bot_token",
    "ua_empty",
    "ua_browser",
    "path_robots",
    "path_wp",
    "path_api",
    "status_error",
    "has_asn",
]

# Label order for softmax
LABEL_ORDER = [
    BotCategory.VERIFIED_SEARCH_CRAWLER.value,
    BotCategory.AI_CRAWLER.value,
    BotCategory.HUMAN_LIKELY.value,
    BotCategory.MONITORING_HEALTH_CHECK.value,
    BotCategory.API_AUTOMATION.value,
    BotCategory.SCRAPER.value,
    BotCategory.UNKNOWN.value,
    BotCategory.UNKNOWN_AUTOMATION.value,
]


def _bundled_coefficients() -> dict[str, Any]:
    """Return intercept + weight matrix for LABEL_ORDER × FEATURE_ORDER."""
    # Rows: labels; cols: features. Tuned for labeled_mini patterns.
    weights = {
        BotCategory.VERIFIED_SEARCH_CRAWLER.value: {
            "ua_bot_token": 2.2,
            "ua_browser": -0.8,
            "path_robots": 1.4,
            "ua_len": 0.01,
        },
        BotCategory.AI_CRAWLER.value: {
            "ua_bot_token": 1.8,
            "path_api": 0.4,
            "ua_browser": -0.5,
        },
        BotCategory.HUMAN_LIKELY.value: {
            "ua_browser": 2.0,
            "ua_bot_token": -2.0,
            "ua_empty": -1.5,
            "path_wp": -0.8,
        },
        BotCategory.MONITORING_HEALTH_CHECK.value: {
            "ua_bot_token": 0.3,
            "path_api": 0.6,
            "ua_len": -0.02,
        },
        BotCategory.API_AUTOMATION.value: {
            "path_api": 1.8,
            "ua_bot_token": 0.5,
            "ua_browser": -1.0,
        },
        BotCategory.SCRAPER.value: {
            "ua_bot_token": 1.2,
            "path_wp": 0.6,
            "ua_browser": -0.4,
        },
        BotCategory.UNKNOWN.value: {
            "ua_empty": 1.0,
            "status_error": 0.4,
        },
        BotCategory.UNKNOWN_AUTOMATION.value: {
            "ua_bot_token": 0.8,
            "ua_empty": 0.6,
            "path_wp": 0.5,
        },
    }
    intercepts = {
        BotCategory.VERIFIED_SEARCH_CRAWLER.value: -0.5,
        BotCategory.AI_CRAWLER.value: -0.4,
        BotCategory.HUMAN_LIKELY.value: 0.2,
        BotCategory.MONITORING_HEALTH_CHECK.value: -0.6,
        BotCategory.API_AUTOMATION.value: -0.5,
        BotCategory.SCRAPER.value: -0.5,
        BotCategory.UNKNOWN.value: 0.0,
        BotCategory.UNKNOWN_AUTOMATION.value: -0.3,
    }
    return {
        "model_id": "feature_logistic_v1",
        "feature_order": FEATURE_ORDER,
        "label_order": LABEL_ORDER,
        "weights": weights,
        "intercepts": intercepts,
        "status": "IMPLEMENTED",
    }


def ml_available() -> bool:
    try:
        import numpy  # noqa: F401
        import sklearn  # noqa: F401

        return True
    except ImportError:
        return False


def _softmax(logits: list[float]) -> list[float]:
    peak = max(logits)
    exps = [math.exp(x - peak) for x in logits]
    total = sum(exps) or 1.0
    return [e / total for e in exps]


@dataclass
class MlPrediction:
    category: str
    score: float
    features: dict[str, float]
    model_id: str
    probabilities: dict[str, float] | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "category": self.category,
            "score": self.score,
            "features": dict(self.features),
            "model_id": self.model_id,
            "probabilities": dict(self.probabilities or {}),
            "status": "IMPLEMENTED",
        }


class MlModel:
    """Bundled feature-logistic classifier; optional sklearn artifact override."""

    def __init__(
        self,
        *,
        model_id: str = "feature_logistic_v1",
        path: Path | None = None,
        backend: Any = None,
        coefficients: dict[str, Any] | None = None,
    ) -> None:
        self.model_id = model_id
        self.path = path
        self._backend = backend
        self._coefficients = coefficients or _bundled_coefficients()
        self.model_id = str(self._coefficients.get("model_id") or model_id)

    @classmethod
    def load(cls, path: str | Path | None = None) -> MlModel:
        if path is None:
            return cls()
        path = Path(path)
        if not path.exists():
            return cls()
        if path.suffix.lower() == ".json":
            meta = json.loads(path.read_text(encoding="utf-8"))
            if "weights" in meta:
                return cls(
                    model_id=str(meta.get("model_id") or path.stem),
                    path=path,
                    coefficients=meta,
                )
            return cls(model_id=str(meta.get("model_id") or path.stem), path=path)
        if ml_available():
            try:
                import joblib  # type: ignore

                backend = joblib.load(path)
                return cls(model_id=path.stem, path=path, backend=backend)
            except Exception:  # noqa: BLE001
                pass
        return cls()

    @classmethod
    def default(cls) -> MlModel:
        return cls()

    def features(self, event: NormalizedEvent) -> dict[str, float]:
        ua = (event.user_agent or "").lower()
        path = (event.path or "").lower()
        browser_tokens = ("mozilla/", "chrome/", "firefox/", "safari/", "edg/")
        return {
            "ua_len": float(len(ua)),
            "ua_bot_token": 1.0
            if any(t in ua for t in ("bot", "crawl", "spider", "slurp", "scrapy", "gptbot"))
            else 0.0,
            "ua_empty": 1.0 if not ua else 0.0,
            "ua_browser": 1.0 if any(t in ua for t in browser_tokens) and "compatible;" not in ua else 0.0,
            "path_robots": 1.0 if "robots.txt" in path else 0.0,
            "path_wp": 1.0 if "wp-" in path or "xmlrpc" in path else 0.0,
            "path_api": 1.0 if "/api" in path or path.startswith("api") else 0.0,
            "status_error": 1.0 if (event.status or 0) >= 400 else 0.0,
            "has_asn": 1.0 if event.asn is not None else 0.0,
        }

    def _predict_logistic(self, feats: dict[str, float]) -> MlPrediction:
        weights = self._coefficients.get("weights") or {}
        intercepts = self._coefficients.get("intercepts") or {}
        labels = list(self._coefficients.get("label_order") or LABEL_ORDER)
        logits: list[float] = []
        for label in labels:
            w = weights.get(label) or {}
            z = float(intercepts.get(label) or 0.0)
            for key, val in feats.items():
                z += float(w.get(key) or 0.0) * float(val)
            logits.append(z)
        probs = _softmax(logits)
        best_i = max(range(len(labels)), key=lambda i: probs[i])
        return MlPrediction(
            category=labels[best_i],
            score=round(probs[best_i], 4),
            features=feats,
            model_id=self.model_id,
            probabilities={labels[i]: round(probs[i], 4) for i in range(len(labels))},
        )

    def predict(self, event: NormalizedEvent) -> MlPrediction | None:
        feats = self.features(event)
        if self._backend is not None and ml_available():
            try:
                import numpy as np

                keys = sorted(feats)
                vec = np.array([[feats[k] for k in keys]])
                if hasattr(self._backend, "predict_proba"):
                    proba = self._backend.predict_proba(vec)[0]
                    idx = int(proba.argmax())
                    label = str(self._backend.classes_[idx])
                    score = float(proba[idx])
                    probs = {
                        str(c): float(p)
                        for c, p in zip(self._backend.classes_, proba)
                    }
                else:
                    label = str(self._backend.predict(vec)[0])
                    score = 0.5
                    probs = {label: score}
                return MlPrediction(
                    category=label,
                    score=score,
                    features=feats,
                    model_id=self.model_id,
                    probabilities=probs,
                )
            except Exception:  # noqa: BLE001
                pass
        return self._predict_logistic(feats)

    def as_classification(self, event: NormalizedEvent) -> ClassificationResult | None:
        pred = self.predict(event)
        if pred is None:
            return None
        try:
            category = BotCategory(pred.category)
        except ValueError:
            category = BotCategory.UNKNOWN
        return ClassificationResult(
            category=category,
            confidence=pred.score,
            evidence=[
                EvidenceItem(
                    statement=(
                        f"ML model {pred.model_id} P={pred.score:.2f} → {pred.category}"
                    ),
                    polarity="for",
                )
            ],
            model_version=MODEL_VERSION,
            ruleset_version=RULESET_VERSION,
            extras={
                "ml": pred.to_dict(),
                "confidence_note": (
                    "ML score is a model probability / decision value from "
                    f"{pred.model_id}; not a calibrated population prevalence."
                ),
            },
        )
