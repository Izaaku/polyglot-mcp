"""
Polyglot MCP — un servidor Model Context Protocol (MCP) que expone el motor
de traducción de Polyglot Talk Tour como herramientas que cualquier modelo de
IA (Claude Desktop, Cursor, etc.) puede descubrir y ejecutar por sí mismo.

Esto NO es "una app que llama a un modelo". Es al revés: el MODELO se conecta
a este servidor, ve las herramientas disponibles (translate, list_languages,
detect_language) y las llama cuando las necesita. Ese es el patrón de MCP.

Correr:
    python server.py            # transporte stdio (para Claude Desktop / Cursor)

Autor: Isaak Uribe · github.com/Izaaku
"""
from mcp.server.fastmcp import FastMCP

import translation

# El nombre con el que el modelo verá este servidor.
mcp = FastMCP("polyglot")


@mcp.tool()
def translate(text: str, target_lang: str, source_lang: str = "auto") -> str:
    """Translate text into a target language.

    Args:
        text: The text to translate.
        target_lang: ISO code of the language to translate into (e.g. "ja", "es", "en").
        source_lang: ISO code of the source language, or "auto" to detect it.

    Returns:
        The translated text.
    """
    return translation.translate(text, target_lang=target_lang, source_lang=source_lang)


@mcp.tool()
def detect_language(text: str) -> str:
    """Detect the language of a piece of text.

    Args:
        text: The text whose language should be detected.

    Returns:
        The ISO code of the detected language (e.g. "es", "en", "ja").
    """
    return translation.detect_language(text)


@mcp.tool()
def list_languages() -> dict:
    """List the languages this translator supports.

    Returns:
        A mapping of ISO language code to human-readable name.
    """
    return translation.list_languages()


if __name__ == "__main__":
    # Transporte por defecto: stdio (el que usan Claude Desktop y Cursor).
    mcp.run()
