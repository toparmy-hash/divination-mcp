# Divination MCP Server 东方术数 MCP

A Model Context Protocol (MCP) server providing traditional Chinese divination tools.

## Tools

### 🔮 ziwei_chart - 紫微斗数排盘
Ziwei Doushu (紫微斗数) birth chart calculation. Input birth date, time, and gender to generate the 12-palace chart with major stars, secondary stars, and four transformations.

### 📜 liuren_chart - 大六壬起盘
Da Liu Ren (大六壬) divination. Generate the heaven plate, earth plate, three transmissions, and four classes for any given date and time.

### ☯️ iching_divine - 易经起卦
I Ching (易经) hexagram reading. Cast a hexagram with moving lines based on a question.

### 📅 huangli_today - 今日黄历
Daily Chinese almanac. Shows auspicious and inauspicious activities for the current day.

## Installation

```bash
pip install fastapi uvicorn pydantic
python mcp_server.py
```

## MCP Connection (SSE)

```json
{
  "mcpServers": {
    "divination": {
      "url": "http://localhost:8787/sse",
      "transport": "sse"
    }
  }
}
```

## About

Built on 2500+ years of Chinese metaphysical tradition. Made accessible for AI agents.

No affiliation with any religious organization. For entertainment and personal insight purposes.
