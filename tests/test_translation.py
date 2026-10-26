"""Tests for the translation engine (translation.py).

Network calls are monkeypatched out, so these run offline and fast.
"""
import pytest

import translation


@pytest.fixture(autouse=True)
def _no_sleep(monkeypatch):
    """Keep retry/backoff loops instant during tests."""
    monkeypatch.setattr(translation.time, "sleep", lambda *_a, **_k: None)


# ---- _g_code: ISO code normalization ----
def test_g_code_blank_is_auto():
    assert translation._g_code("") == "auto"
    assert translation._g_code(None) == "auto"


def test_g_code_normalizes_chinese_variants():
    assert translation._g_code("zh") == "zh-CN"
    assert translation._g_code("zh_cn") == "zh-CN"
    assert translation._g_code("ZH-CN") == "zh-CN"
    assert translation._g_code("zh-hant") == "zh-TW"
    assert translation._g_code("zh_tw") == "zh-TW"


def test_g_code_lowercases_plain_codes():
    assert translation._g_code("EN") == "en"
    assert translation._g_code("  Es ") == "es"


# ---- _heuristic_lang: cheap es/en fallback ----
def test_heuristic_lang_detects_spanish():
    assert translation._heuristic_lang("hola, ¿cómo estás?") == "es"
    assert translation._heuristic_lang("el gato y la casa") == "es"


def test_heuristic_lang_defaults_to_english():
    assert translation._heuristic_lang("the quick brown fox") == "en"
    assert translation._heuristic_lang("") == "en"


# ---- list_languages ----
def test_list_languages_has_expected_entries():
    langs = translation.list_languages()
    assert langs["es"] == "Spanish"
    assert langs["en"] == "English"
    assert langs["ja"] == "Japanese"


def test_list_languages_returns_a_copy():
    langs = translation.list_languages()
    langs["es"] = "mutated"
    assert translation.list_languages()["es"] == "Spanish"


# ---- translate: provider cascade ----
def test_translate_empty_text_returns_empty():
    assert translation.translate("", "es") == ""
    assert translation.translate("   ", "es") == ""


def test_translate_prefers_mymemory(monkeypatch):
    monkeypatch.setattr(translation, "_mymemory", lambda text, src, tgt: "hola mundo")

    def _should_not_run(*_a, **_k):
        raise AssertionError("Google must not be called when MyMemory succeeds")

    monkeypatch.setattr(translation, "_google", _should_not_run)
    assert translation.translate("hello world", "es") == "hola mundo"


def test_translate_falls_back_to_google(monkeypatch):
    monkeypatch.setattr(translation, "_mymemory", lambda text, src, tgt: None)
    monkeypatch.setattr(translation, "_google", lambda text, src, tgt: ("hola", None))
    assert translation.translate("hello", "es") == "hola"


def test_translate_raises_when_all_providers_fail(monkeypatch):
    monkeypatch.setattr(translation, "_mymemory", lambda text, src, tgt: None)
    monkeypatch.setattr(translation, "_google", lambda text, src, tgt: (None, "HTTP 429"))
    with pytest.raises(RuntimeError):
        translation.translate("hello", "es")


# ---- detect_language ----
def test_detect_language_empty_returns_und():
    assert translation.detect_language("") == "und"


def test_detect_language_reads_google_response(monkeypatch):
    fake = [[["hi", "hola"]], None, "es"]
    monkeypatch.setattr(translation, "_http_json", lambda url, timeout=10: fake)
    assert translation.detect_language("hola") == "es"


def test_detect_language_falls_back_to_heuristic(monkeypatch):
    def _down(*_a, **_k):
        raise RuntimeError("network down")

    monkeypatch.setattr(translation, "_http_json", _down)
    assert translation.detect_language("hola, ¿cómo estás?") == "es"
