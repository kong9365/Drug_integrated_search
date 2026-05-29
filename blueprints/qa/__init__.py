"""
KD-IRIS 1차 빌드 — 의약품QA blueprint (기능재설계 v2 §11)

자사 품목 마스터(SQLite) × Enrichment × 모니터링 × 판단·행동.
url_prefix=/app/qa
"""
from flask import Blueprint

qa_bp = Blueprint("qa", __name__, url_prefix="/app/qa")

# 라우트 등록 (순환 import 회피 — blueprint 정의 후 import)
from . import views  # noqa: E402,F401
