# Divination MCP Server 东方术数 MCP

A Model Context Protocol (MCP) server providing traditional Chinese divination tools.

## 🚀 Try it instantly (public beta)

No installation needed. Add to your MCP client:

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

Free public beta. No rate limits for now.

## 🔮 Tools

- **ziwei_chart** — Ziwei Doushu (紫微斗数) birth chart
- **liuren_chart** — Da Liu Ren (大六壬) divination
- **iching_divine** — I Ching (易经) hexagram reading
- **huangli_today** — Daily almanac (黄历)

## 📦 Self-host

```bash
pip install fastapi uvicorn pydantic
python mcp_server.py
```

## About

The most interesting MCPs won't be developer tools. They'll be perspective tools.

Divination doesn't predict the future. It reframes the question.
