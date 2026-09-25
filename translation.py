"""
Motor de traducción de Polyglot Talk Tour, extraído como módulo reutilizable.

Usa el mismo endpoint gratuito de Google Translate que la cascada de PTT
(translate.googleapis.com/translate_a/single). No requiere API key ni el
backend completo de Flask/Supabase: es una versión limpia y autónoma para
poder envolverla con MCP y demostrarla.

Si algún día quieres apuntar el MCP server a tu backend real de PTT en vez
de a este endpoint, solo cambias `translate()` por una llamada HTTP a tu API.
"""
import json
import urllib.parse
import urllib.request

_UA = {"User-Agent": "Mozilla/5.0 (compatible; PolyglotMCP/1.0)"}

# Idiomas soportados (subconjunto representativo de PTT). Código ISO -> nombre.
LANGUAGES = {
    "es": "Spanish",
    "en": "English",
    "fr": "French",
    "de": "German",
    "it": "Italian",
    "pt": "Portuguese",
    "ja": "Japanese",
    "ko": "Korean",
    "zh-CN": "Chinese (Simplified)",
    "zh-TW": "Chinese (Traditional)",
    "ar": "Arabic",
    "ru": "Russian",
    "hi": "Hindi",
    "nl": "Dutch",
    "tr": "Turkish",
    "pl": "Polish",
    "vi": "Vietnamese",
    "th": "Thai",
    "id": "Indonesian",
    "uk": "Ukrainian",
}


def _g_code(code: str) -> str:
    """Normaliza códigos de idioma al formato que espera Google."""
    if not code:
        return "auto"
    c = code.strip()
    low = c.lower()
    if low in ("zh", "zh-hans", "zh_cn", "zh-cn"):
        return "zh-CN"
    if low in ("zh-hant", "zh_tw", "zh-tw"):
        return "zh-TW"
    return low


def translate(text: str, target_lang: str, source_lang: str = "auto") -> str:
    """Traduce `text` a `target_lang`. `source_lang='auto'` detecta el idioma.

    Devuelve el texto traducido. Lanza RuntimeError si la traducción falla.
    """
    if not text or not text.strip():
        return ""

    src = _g_code(source_lang)
    tgt = _g_code(target_lang)

    params = urllib.parse.urlencode({
        "client": "gtx",
        "sl": src,
        "tl": tgt,
        "dt": "t",
        "q": text,
    })
    url = "https://translate.googleapis.com/translate_a/single?" + params

    try:
        req = urllib.request.Request(url, headers=_UA)
        with urllib.request.urlopen(req, timeout=10) as resp:
            data = json.load(resp)
        # La respuesta es una lista anidada; los segmentos están en data[0].
        segments = data[0] or []
        return "".join(seg[0] for seg in segments if seg and seg[0])
    except Exception as e:
        raise RuntimeError(f"translation failed: {e}") from e


def detect_language(text: str) -> str:
    """Detecta el idioma de `text`. Devuelve un código ISO (p. ej. 'es', 'en')."""
    if not text or not text.strip():
        return "und"

    params = urllib.parse.urlencode({
        "client": "gtx",
        "sl": "auto",
        "tl": "en",
        "dt": "t",
        "q": text,
    })
    url = "https://translate.googleapis.com/translate_a/single?" + params

    try:
        req = urllib.request.Request(url, headers=_UA)
        with urllib.request.urlopen(req, timeout=10) as resp:
            data = json.load(resp)
        # El código detectado suele venir en data[2].
        detected = data[2] if len(data) > 2 else None
        return detected or "und"
    except Exception as e:
        raise RuntimeError(f"detection failed: {e}") from e


def list_languages() -> dict:
    """Devuelve el mapa de idiomas soportados (código ISO -> nombre en inglés)."""
    return dict(LANGUAGES)
