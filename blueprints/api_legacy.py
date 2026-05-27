"""
RegHub 360 — 기존 API 엔드포인트 (구 app.py /api/* 유지)
프론트엔드 라이브 데모 및 부분 갱신용.
"""
from flask import Blueprint, request, jsonify, send_from_directory
import logging

from ..config import IMAGES_FOLDER
from ..api_client import fetch_approval, fetch_identification, search_all

logger = logging.getLogger(__name__)

api_bp = Blueprint("api", __name__, url_prefix="/api")


@api_bp.route("/search", methods=["GET"])
def api_search():
    item_seq = request.args.get("item_seq", "").strip() or None
    item_name = request.args.get("item_name", "").strip() or None
    entp_name = request.args.get("entp_name", "").strip() or None
    download_images = request.args.get("download_images", "true").lower() == "true"

    if not (item_seq or item_name or entp_name):
        return jsonify({"success": False, "error": "검색어를 입력해주세요."}), 400

    try:
        results = search_all(
            item_seq=item_seq,
            item_name=item_name,
            entp_name=entp_name,
            download_images=download_images,
        )
        return jsonify({
            "success": True,
            "query": {"item_name": item_name, "entp_name": entp_name},
            "results": results,
        })
    except Exception as e:
        logger.error(f"검색 오류: {e}")
        return jsonify({"success": False, "error": str(e)}), 500


@api_bp.route("/approval", methods=["GET"])
def api_approval():
    item_name = request.args.get("item_name", "").strip() or None
    entp_name = request.args.get("entp_name", "").strip() or None
    page_no = int(request.args.get("page_no", 1))
    num_of_rows = int(request.args.get("num_of_rows", 10))
    return jsonify(fetch_approval(
        item_name=item_name, entp_name=entp_name,
        page_no=page_no, num_of_rows=num_of_rows,
    ))


@api_bp.route("/identification", methods=["GET"])
def api_identification():
    item_name = request.args.get("item_name", "").strip() or None
    entp_name = request.args.get("entp_name", "").strip() or None
    page_no = int(request.args.get("page_no", 1))
    num_of_rows = int(request.args.get("num_of_rows", 10))
    download_images = request.args.get("download_images", "true").lower() == "true"
    return jsonify(fetch_identification(
        item_name=item_name, entp_name=entp_name,
        page_no=page_no, num_of_rows=num_of_rows,
        download_images=download_images,
    ))


@api_bp.route("/images/<filename>")
def serve_image(filename):
    return send_from_directory(str(IMAGES_FOLDER), filename)
