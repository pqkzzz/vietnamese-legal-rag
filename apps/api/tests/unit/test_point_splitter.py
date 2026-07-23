"""Tests for Vietnamese legal point splitting."""

from __future__ import annotations

import sys
from pathlib import Path

API_ROOT = Path(__file__).resolve().parents[2]
if str(API_ROOT) not in sys.path:
    sys.path.insert(0, str(API_ROOT))

from app.modules.legal_parser.point_splitter import split_clause_points
from app.utils.identifiers import make_point_chunk_id


def test_splits_a_b_c_points() -> None:
    text = "2. Các trường hợp sau đây:\n\na) Một;\n\nb) Hai;\n\nc) Ba."

    result = split_clause_points(text, text)

    assert result.was_split is True
    assert [point.point_number for point in result.points] == ["a", "b", "c"]


def test_splits_d_and_vietnamese_dd_as_distinct_points() -> None:
    text = "1. Gồm:\n\na) A;\n\nb) B;\n\nc) C;\n\nd) D;\n\nđ) Đ."

    result = split_clause_points(text, text)

    assert [point.point_number for point in result.points][-2:] == ["d", "đ"]
    assert result.points[-1].content_clean.startswith("đ)")


def test_vietnamese_dd_maps_to_ddd_suffix() -> None:
    assert make_point_chunk_id("LKDBDS_2023_D1_K2", "đ") == "LKDBDS_2023_D1_K2_DDD"


def test_does_not_split_single_marker() -> None:
    text = "1. Chỉ có một điểm:\n\na) Nội dung."

    assert split_clause_points(text, text).was_split is False


def test_does_not_split_marker_in_middle_of_sentence() -> None:
    text = "Tổ chức loại a) được áp dụng trong trường hợp này, còn b) là ví dụ khác."

    assert split_clause_points(text, text).was_split is False


def test_does_not_split_invalid_marker_sequence() -> None:
    text = "1. Gồm:\n\na) A;\n\nc) C;\n\nb) B."

    result = split_clause_points(text, text)

    assert result.was_split is False
    assert result.warnings[0]["code"] == "INVALID_POINT_SEQUENCE"


def test_preserves_vietnamese_unicode() -> None:
    text = "1. Gồm:\n\na) Quyền sử dụng đất;\n\nb) Nhà ở Việt Nam."

    result = split_clause_points(text, text)

    assert "Quyền sử dụng đất" in result.points[0].content_clean
    assert "Việt Nam" in result.points[1].content_clean


def test_preserves_raw_content_inside_point() -> None:
    raw = "1. Gồm:\n\na) Nội dung[2] thô;\n\nb) Nội dung khác."
    clean = "1. Gồm:\n\na) Nội dung thô;\n\nb) Nội dung khác."

    result = split_clause_points(raw, clean)

    assert "[2]" in result.points[0].content_raw
    assert "[2]" not in result.points[0].content_clean


def test_splits_clause_lead_correctly() -> None:
    text = "2. Luật này không điều chỉnh đối với các trường hợp sau đây:\n\na) A;\n\nb) B."

    result = split_clause_points(text, text)

    assert result.clause_lead_clean == "2. Luật này không điều chỉnh đối với các trường hợp sau đây:"
    assert "a)" not in result.clause_lead_clean


def test_does_not_drop_punctuation() -> None:
    text = "1. Gồm:\n\na) A, B; C.\n\nb) D: E."

    result = split_clause_points(text, text)

    assert result.points[0].content_clean.endswith("C.")
    assert "D: E." in result.points[1].content_clean


def test_does_not_split_numeric_lists() -> None:
    text = "1. Danh sách:\n\n1) Một;\n\n2) Hai;\n\n3) Ba."

    assert split_clause_points(text, text).was_split is False


def test_handles_indented_markers() -> None:
    text = "1. Gồm:\n\n    a) A;\n\t b) B."

    result = split_clause_points(text, text)

    assert result.was_split is True
    assert [point.point_number for point in result.points] == ["a", "b"]


def test_handles_multiple_blank_lines() -> None:
    text = "1. Gồm:\n\n\n\na) A;\n\n\n\nb) B."

    result = split_clause_points(text, text)

    assert result.was_split is True
    assert result.points[0].content_clean == "a) A;"


def test_does_not_split_parenthesized_example_mid_sentence() -> None:
    text = "Ví dụ (a) không phải marker đầu dòng và b) cũng nằm giữa câu."

    assert split_clause_points(text, text).was_split is False
