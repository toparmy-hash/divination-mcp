# Divination MCP Server 🔮 东方术数 MCP

A Model Context Protocol (MCP) server providing traditional Chinese divination tools.

**The most interesting MCPs won't be developer tools. They'll be perspective tools.**

Divination doesn't predict the future. It reframes the question.

## ✨ Features

- **Ziwei Doushu (紫微斗数)** — Chinese astrology birth chart with 12 palaces
- **Da Liu Ren (大六壬)** — Ancient Chinese divination system, 天地盘/三传/四课
- **I Ching (易经)** — 64 hexagram divination with changing lines
- **Daily Almanac (黄历)** — Traditional Chinese calendar with auspicious/inauspicious activities

## 🚀 Try it instantly (Free Public Beta)

No installation needed. Add to your MCP client (Claude Desktop, Cursor, Codex, etc.):

```json
{
  "mcpServers": {
    "divination": {
      "url": "https://shows-interference-mask-wright.trycloudflare.com/sse",
      "transport": "sse"
    }
  }
}
```

**Free tier:** 10 calls/day (anonymous, no API key needed)

**Pro tier:** Unlimited access — contact for API key (coming soon with x402 micropayments)

## 📦 Self-host

```bash
pip install fastapi uvicorn pydantic
python mcp_server_v2.py
```

## 🛠️ Tools

| Tool | Description | Price |
|------|-------------|-------|
| `ziwei_chart` | Ziwei Doushu birth chart | Free beta |
| `liuren_chart` | Da Liu Ren divination | Free beta |
| `iching_divination` | I Ching hexagram reading | Free beta |
| `daily_almanac` | Daily almanac (黄历) | Always free |

## 🔮 Why this exists

I'm a Chinese metaphysics practitioner building tools for AI agents. The West builds AI that optimizes. The East builds systems that see. This is a bridge.

Most MCP servers give you more data. This one gives you a different lens.

## 📊 Status

- **Version:** 0.2.0
- **Status:** Public beta
- **Transport:** SSE
- **Auth:** API key (coming: x402 per-call micropayments)

## About

Built and maintained by Lingyi (灵屹). Open source, free to use during beta.

GitHub: https://github.com/toparmy-hash/divination-mcp
