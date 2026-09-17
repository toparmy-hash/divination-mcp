# Divination MCP Server 东方术数 MCP

A Model Context Protocol (MCP) server providing traditional Chinese divination tools.

## 🚀 Try it instantly (public beta)

No installation needed. Add this to your MCP client config:

```json
{
  "mcpServers": {
    "divination": {
      "url": "https://metric-arts-pupils-them.trycloudflare.com/sse",
      "transport": "sse"
    }
  }
}
```

> **Note:** Free public beta. No rate limits for now. If it gets popular I'll figure out pricing.

## 🔮 Tools

### ziwei_chart — 紫微斗数排盘
Ziwei Doushu birth chart. 12 palaces, major stars, secondary stars, four transformations.

### liuren_chart — 大六壬起盘
Da Liu Ren divination. Heaven plate, earth plate, three transmissions, four classes.

### iching_divine — 易经起卦
I Ching hexagram reading with moving lines.

### huangli_today — 今日黄历
Daily Chinese almanac. Auspicious/inauspicious activities.

## 📦 Self-host

```bash
pip install fastapi uvicorn pydantic
python mcp_server.py
```

Connect via `http://localhost:8788/sse`

## About

Built on 2500+ years of Chinese metaphysical tradition. Made accessible for AI agents.

The most interesting MCPs won't be developer tools. They'll be perspective tools.

Divination doesn't predict the future. It reframes the question.
