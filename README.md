# Polyglot MCP

![CI](https://github.com/Izaaku/polyglot-mcp/actions/workflows/ci.yml/badge.svg)

An **MCP (Model Context Protocol) server** that exposes the translation engine
from [Polyglot Talk Tour](https://polyglot-talk.fly.dev/tour) as tools that any
AI model — Claude Desktop, Cursor, or a custom agent — can discover and call on
its own.

> **What makes this MCP and not just "an API":** the AI model is the *client*.
> It connects to this server, sees the available tools, and decides when to call
> them. The app doesn't call the model — the model calls the tools. That's the
> whole point of the Model Context Protocol.

Built by Isaak Uribe · [github.com/Izaaku](https://github.com/Izaaku)

## Tools exposed

| Tool | What it does |
|------|--------------|
| `translate(text, target_lang, source_lang="auto")` | Translate text into a target language |
| `detect_language(text)` | Detect the language of a piece of text |
| `list_languages()` | List supported languages (ISO code → name) |

The translation engine (`translation.py`) mirrors the free-endpoint cascade used
in Polyglot Talk Tour, packaged as a standalone module so the server runs without
the full Flask/Supabase backend. To point it at the production PTT backend
instead, swap the body of `translate()` for an HTTP call to your API.

## Run it

```bash
# 1. Install the MCP SDK
pip install -r requirements.txt

# 2. Start the server (stdio transport — used by Claude Desktop / Cursor)
python server.py
```

The server speaks MCP over stdio, so you normally don't run it by hand — you
point an MCP client at it (below).

## Connect it to Claude Desktop

1. Open Claude Desktop → **Settings → Developer → Edit Config**.
2. Add this server (see `claude_desktop_config.example.json`), adjusting the path:

```json
{
  "mcpServers": {
    "polyglot": {
      "command": "python",
      "args": ["C:\\Users\\izaak\\polyglot-mcp\\server.py"]
    }
  }
}
```

3. Restart Claude Desktop. You'll see a 🔌 tools icon.
4. Ask Claude: *"Use the polyglot tools to translate 'good morning' into Japanese."*
   Claude will call your `translate` tool and return **おはよう**.

## Test it without an AI client

```bash
pip install "mcp[cli]"
mcp dev server.py     # opens the MCP Inspector to call the tools by hand
```

## How it works (architecture)

```
  ┌────────────────┐   MCP (JSON-RPC over stdio)   ┌──────────────────┐
  │  AI model /    │ ───── "list tools" ─────────▶ │  Polyglot MCP    │
  │  agent (client)│ ◀──── translate/detect/… ──── │  server.py       │
  └────────────────┘                               └────────┬─────────┘
                                                            │ calls
                                                   ┌────────▼─────────┐
                                                   │ translation.py   │
                                                   │ (PTT engine)     │
                                                   └──────────────────┘
```

## Tests

```bash
pip install -r requirements.txt -r requirements-dev.txt
pytest
```

The suite monkeypatches the network out, so it runs offline and fast. CI runs it
on Python 3.10–3.12 via GitHub Actions on every push and pull request.

## License

MIT
