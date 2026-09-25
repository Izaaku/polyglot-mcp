"""
Motor de traducción de Polyglot Talk Tour, extraído como módulo reutilizable.

Estrategia de proveedores (robusta, misma filosofía que la cascada de PTT):
  1. MyMemory (API pública, tolerante para volumen bajo)  -> PRINCIPAL
  2. Google (endpoint gratuito) con reintento + backoff    -> RESPALDO
Si ambos fallan, se lanza un error claro que nombra a los dos.

Se prioriza MyMemory porque el endpoint gratuito de Google limita por IP
(HTTP 429) cuando recibe muchas llamadas seguidas.
"""
import json
import time
import urllib.parse
import urllib.request
import urllib.error

_UA = {"User-Agent": "Mozilla/5.0 (compatible; PolyglotMCP/1.2)"}

LANGUAGES = {
    "es": "Spanish", "en": "English", "fr": "French", "de": "German",
    "it": "Italian", "pt": "Portuguese", "ja": "Japanese", "ko": "Korean",
    "zh-CN": "Chinese (Simplified)", "zh-TW": "Chinese (Traditional)",
    "ar": "Arabic", "ru": "Russian", "hi": "Hindi", "nl": "Dutch",
    "tr": "Turkish", "pl": "Polish", "vi": "Vietnamese", "th": "Thai",
    "id": "Indonesian", "uk": "Ukrainian",
}

_RETRY_WAITS = (0.6, 1.4, 3.0)


def _g_code(code: str) -> str:
    if not code:
        return "auto"
    low = code.strip().lower()
    if low in ("zh", "zh-hans", "zh_cn", "zh-cn"):
        return "zh-CN"
    if low in ("zh-hant", "zh_tw", "zh-tw"):
        return "zh-TW"
    return low


def _http_json(url: str, timeout: int = 10):
    req = urllib.request.Request(url, headers=_UA)
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        return json.load(resp)


# ---- Proveedor PRINCIPAL: MyMemory ----
def _mymemory(text: str, src: str, tgt: str):
    params = urllib.parse.urlencode({"q": text, "langpair": "%s|%s" % (src, tgt)})
    url = "https://api.mymemory.translated.net/get?" + params
    try:
        data = _http_json(url)
        if data.get("responseStatus") not in (200, "200", None):
            return None
        out = (data.get("responseData") or {}).get("translatedText")
        if out and "MYMEMORY WARNING" not in out.upper():
            return out
        return None
    except Exception:
        return None


# ---- Proveedor RESPALDO: Google (con reintento/backoff) ----
def _google(text: str, src: str, tgt: str):
    params = urllib.parse.urlencode({
        "client": "gtx", "sl": src, "tl": tgt, "dt": "t", "q": text,
    })
    url = "https://translate.googleapis.com/translate_a/single?" + params
    last_err = None
    for wait in (0.0,) + _RETRY_WAITS:
        if wait:
            time.sleep(wait)
        try:
            data = _http_json(url)
            return "".join(seg[0] for seg in (data[0] or []) if seg and seg[0]), None
        except urllib.error.HTTPError as e:
            last_err = "HTTP %s" % e.code
            if e.code not in (429, 500, 502, 503):
                break
        except Exception as e:
            last_err = str(e)
    return None, last_err


def _heuristic_lang(text: str) -> str:
    t = (text or "").lower()
    if any(w in t for w in (" el ", " la ", " los ", " que ", " de ", " y ", "ñ", "¿", "¡", "á", "í", "ó", "ú")):
        return "es"
    return "en"


def translate(text: str, target_lang: str, source_lang: str = "auto") -> str:
    """Traduce `text` a `target_lang`. MyMemory (principal) -> Google (respaldo)."""
    if not text or not text.strip():
        return ""
    tgt = _g_code(target_lang)
    src = _g_code(source_lang)
    src_resolved = src if src != "auto" else _heuristic_lang(text)

    # 1) MyMemory (principal)
    out = _mymemory(text, src_resolved, tgt)
    if out:
        return out

    # 2) Google (respaldo, con reintento)
    out, err = _google(text, src, tgt)
    if out:
        return out

    raise RuntimeError(
        "translation failed: MyMemory returned nothing and Google error was %s" % err
    )


def detect_language(text: str) -> str:
    """Detecta el idioma de `text`. Google con reintento; si falla, heurística es/en."""
    if not text or not text.strip():
        return "und"
    params = urllib.parse.urlencode({
        "client": "gtx", "sl": "auto", "tl": "en", "dt": "t", "q": text,
    })
    url = "https://translate.googleapis.com/translate_a/single?" + params
    for wait in (0.0,) + _RETRY_WAITS:
        if wait:
            time.sleep(wait)
        try:
            data = _http_json(url)
            return (data[2] if len(data) > 2 else None) or "und"
        except Exception:
            continue
    return _heuristic_lang(text)


def list_languages() -> dict:
    return dict(LANGUAGES)
