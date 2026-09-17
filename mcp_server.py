#!/usr/bin/env python3
"""
术数 MCP 服务器 v0.2.0 - 支持 API key + 用量统计 + 免费额度
Model Context Protocol: https://modelcontextprotocol.io/
"""
import json
import os
import sys
import uuid
import time
from fastapi import FastAPI, Request, Header, HTTPException
from fastapi.responses import StreamingResponse, JSONResponse
from pydantic import BaseModel
from typing import Optional, Dict
from datetime import datetime, date as date_obj

app = FastAPI(title="东方术数 MCP Server", version="0.2.0")

# === 配置 ===
SERVER_INFO = {
    "name": "divination-mcp",
    "version": "0.2.0",
    "description": "东方术数 MCP 服务 - 紫微斗数/大六壬/易经/黄历",
}

FREE_DAILY_LIMIT = 10  # 免费用户每日调用上限
STORAGE_FILE = os.environ.get("MCP_STORAGE", "/tmp/mcp_usage.json")

# === 工具定义 ===
TOOLS = [
    {
        "name": "ziwei_chart",
        "description": "紫微斗数排盘。输入出生年月日时性别，排出十二宫、主星、四化等基本命盘信息。",
        "inputSchema": {
            "type": "object",
            "properties": {
                "date": {"type": "string", "description": "出生日期，格式 YYYY-MM-DD"},
                "time": {"type": "string", "description": "出生时间，格式 HH:MM"},
                "gender": {"type": "string", "description": "性别：male/female"},
                "timezone": {"type": "string", "description": "时区，默认 Asia/Shanghai"},
                "longitude": {"type": "number", "description": "出生地经度，默认 120.0"},
            },
            "required": ["date", "time", "gender"],
        },
    },
    {
        "name": "liuren_chart",
        "description": "大六壬起盘。输入日期和时辰，排出天地盘、三传、四课、六亲等。",
        "inputSchema": {
            "type": "object",
            "properties": {
                "date": {"type": "string", "description": "日期，格式 YYYY-MM-DD"},
                "hour": {"type": "integer", "description": "时辰（小时，0-23）"},
                "question": {"type": "string", "description": "所问之事（可选）"},
            },
            "required": ["date", "hour"],
        },
    },
    {
        "name": "iching_divination",
        "description": "易经起卦。输入问题，随机起卦给出本卦、变爻、上下卦。",
        "inputSchema": {
            "type": "object",
            "properties": {
                "question": {"type": "string", "description": "要问的问题"},
            },
            "required": ["question"],
        },
    },
    {
        "name": "daily_almanac",
        "description": "今日黄历宜忌。返回当日天干地支、五行、宜、忌。",
        "inputSchema": {
            "type": "object",
            "properties": {
                "date": {"type": "string", "description": "日期，格式 YYYY-MM-DD，默认今天"},
            },
            "required": [],
        },
    },
]

# === 用量存储 ===
def load_usage():
    if os.path.exists(STORAGE_FILE):
        try:
            with open(STORAGE_FILE, 'r') as f:
                return json.load(f)
        except:
            pass
    return {"users": {}, "total_calls": 0, "api_keys": {}}

def save_usage(data):
    with open(STORAGE_FILE, 'w') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

def get_today_str():
    return datetime.now().strftime("%Y-%m-%d")

def check_and_record(api_key: str = "anonymous"):
    """检查用量并记录调用。返回 (允许: bool, 剩余次数: int)"""
    data = load_usage()
    today = get_today_str()
    
    if api_key not in data["users"]:
        data["users"][api_key] = {"daily": {}, "total": 0, "created": today}
    
    user = data["users"][api_key]
    if today not in user["daily"]:
        user["daily"][today] = 0
    
    # API key用户无限制（假设是付费或白名单）
    # anonymous用户有免费额度
    if api_key == "anonymous" and user["daily"][today] >= FREE_DAILY_LIMIT:
        remaining = 0
        allowed = False
    else:
        user["daily"][today] += 1
        user["total"] += 1
        data["total_calls"] += 1
        remaining = FREE_DAILY_LIMIT - user["daily"][today] if api_key == "anonymous" else -1
        allowed = True
    
    save_usage(data)
    return allowed, remaining

# SSE 会话存储
sessions = {}


@app.get("/")
async def root():
    data = load_usage()
    return {
        "name": SERVER_INFO["name"],
        "version": SERVER_INFO["version"],
        "description": SERVER_INFO["description"],
        "tools": len(TOOLS),
        "total_calls": data.get("total_calls", 0),
        "free_daily_limit": FREE_DAILY_LIMIT,
        "sse_endpoint": "/sse",
        "mcp_endpoint": "/mcp",
    }


@app.get("/sse")
async def sse_endpoint(request: Request):
    """MCP SSE 连接端点"""
    session_id = str(uuid.uuid4())
    sessions[session_id] = {"initialized": False}
    
    async def event_generator():
        yield f"event: endpoint\ndata: /mcp?sessionId={session_id}\n\n"
        import asyncio
        while True:
            await asyncio.sleep(30)
            yield ": ping\n\n"
    
    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "Connection": "keep-alive"},
    )


@app.post("/mcp")
async def mcp_endpoint(request: Request, x_api_key: Optional[str] = Header(None)):
    """MCP 消息端点"""
    body = await request.json()
    method = body.get("method", "")
    params = body.get("params", {})
    request_id = body.get("id")
    api_key = x_api_key or "anonymous"
    
    result = None
    
    if method == "initialize":
        result = {
            "protocolVersion": "2024-11-05",
            "capabilities": {"tools": {}},
            "serverInfo": SERVER_INFO,
        }
    elif method == "tools/list":
        result = {"tools": TOOLS}
    elif method == "tools/call":
        tool_name = params.get("name", "")
        arguments = params.get("arguments", {})
        
        # 用量检查
        allowed, remaining = check_and_record(api_key)
        if not allowed:
            return JSONResponse({
                "jsonrpc": "2.0",
                "id": request_id,
                "result": {
                    "content": [{"type": "text", "text": json.dumps({
                        "error": "Daily free limit reached",
                        "message": f"Free tier limit of {FREE_DAILY_LIMIT} calls/day reached. Get an API key for unlimited access.",
                        "remaining": 0,
                        "upgrade_url": "https://github.com/toparmy-hash/divination-mcp"
                    }, ensure_ascii=False)}],
                    "isError": True,
                }
            })
        
        result = await call_tool(tool_name, arguments)
        # 在结果里加用量信息
        if isinstance(result, dict) and "content" in result and result["content"]:
            # 不改动原始结果，只加header
            pass
    elif method == "notifications/initialized":
        return JSONResponse({})
    else:
        return JSONResponse({
            "jsonrpc": "2.0",
            "id": request_id,
            "error": {"code": -32601, "message": f"Method not found: {method}"}
        }, status_code=400)
    
    return JSONResponse({
        "jsonrpc": "2.0",
        "id": request_id,
        "result": result,
    })


async def call_tool(name: str, args: dict):
    """调用工具"""
    import subprocess
    
    if name == "ziwei_chart":
        script = "/Users/liuyang/.openclaw/workspace/skills/ziwei-doushu/scripts/ziwei_chart.py"
        cmd = [
            sys.executable, script,
            "--date", args.get("date", ""),
            "--time", args.get("time", ""),
            "--gender", args.get("gender", "male"),
            "--timezone", args.get("timezone", "Asia/Shanghai"),
            "--longitude", str(args.get("longitude", 120.0)),
            "--format", "json",
            "--template", "lite",
            "--engine", "py",
        ]
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
        data = json.loads(result.stdout)
        zw = data.get("ziwei", data)
        palaces = []
        for p in zw.get("palaces", []):
            palaces.append({
                "name": p.get("name", ""),
                "stem_branch": f"{p.get('stem','')}{p.get('branch','')}",
                "major_stars": [s.get("name","") for s in p.get("major_stars", [])],
            })
        return {
            "content": [{"type": "text", "text": json.dumps({
                "service": "紫微斗数排盘",
                "basic_info": {
                    "five_elements_class": zw.get("five_elements_class", ""),
                    "ming_palace": f"{zw.get('ming',{}).get('stem','')}{zw.get('ming',{}).get('branch','')}",
                },
                "twelve_palaces": palaces,
            }, ensure_ascii=False, indent=2)}]
        }
    
    elif name == "liuren_chart":
        script = "/Users/liuyang/.openclaw/workspace/projects/divination-mcp/liuren.py"
        dt = datetime.strptime(args.get("date", ""), "%Y-%m-%d")
        cmd = [
            sys.executable, script,
            str(dt.year), str(dt.month), str(dt.day),
            str(args.get("hour", 12)),
            "--json",
        ]
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=30,
                              cwd=os.path.dirname(script))
        data = json.loads(result.stdout)
        return {
            "content": [{"type": "text", "text": json.dumps({
                "service": "大六壬起盘",
                "time": data.get("时间", ""),
                "四柱": data.get("四柱", {}),
                "月将": data.get("月将", ""),
                "旬空": data.get("旬空", []),
                "三传": data.get("三传", []),
                "四课": data.get("四课", []),
            }, ensure_ascii=False, indent=2)}]
        }
    
    elif name == "iching_divination":
        import random
        lines = []
        for _ in range(6):
            coins = [random.choice([2, 3]) for _ in range(3)]
            lines.append(sum(coins))
        lines.reverse()
        
        trigrams = {
            (7,7,7): ("乾", "☰", "天"),
            (7,7,8): ("兑", "☱", "泽"),
            (7,8,7): ("离", "☲", "火"),
            (7,8,8): ("震", "☳", "雷"),
            (8,7,7): ("巽", "☴", "风"),
            (8,7,8): ("坎", "☵", "水"),
            (8,8,7): ("艮", "☶", "山"),
            (8,8,8): ("坤", "☷", "地"),
        }
        
        def yao_val(l):
            if l in [6, 8]: return 8
            if l in [7, 9]: return 7
            return l
        
        lower = tuple(yao_val(l) for l in lines[:3])
        upper = tuple(yao_val(l) for l in lines[3:])
        lower_name, lower_sym, lower_ele = trigrams.get(lower, ("?", "?", "?"))
        upper_name, upper_sym, upper_ele = trigrams.get(upper, ("?", "?", "?"))
        changing = [i+1 for i, l in enumerate(lines) if l in [6, 9]]
        
        return {
            "content": [{"type": "text", "text": json.dumps({
                "service": "易经起卦",
                "question": args.get("question", ""),
                "hexagram": f"{upper_name}{lower_name}",
                "upper": f"{upper_name} {upper_sym} ({upper_ele})",
                "lower": f"{lower_name} {lower_sym} ({lower_ele})",
                "changing_lines": changing,
                "note": "此为起卦结果，解读需结合卦辞爻辞具体分析。",
            }, ensure_ascii=False, indent=2)}]
        }
    
    elif name == "daily_almanac":
        if args.get("date"):
            d = datetime.strptime(args["date"], "%Y-%m-%d").date()
        else:
            d = date_obj.today()
        
        stems = ["甲","乙","丙","丁","戊","己","庚","辛","壬","癸"]
        branches = ["子","丑","寅","卯","辰","巳","午","未","申","酉","戌","亥"]
        
        base = date_obj(2000, 1, 1)
        delta = (d - base).days
        stem_idx = (6 + delta) % 10
        branch_idx = (4 + delta) % 12
        day_gz = f"{stems[stem_idx]}{branches[branch_idx]}"
        
        return {
            "content": [{"type": "text", "text": json.dumps({
                "service": "今日黄历",
                "date": d.isoformat(),
                "ganzhi": day_gz,
                "yi": ["祭祀", "祈福", "求嗣"],
                "ji": ["动土", "嫁娶"],
                "note": "简化版黄历，仅供参考。",
            }, ensure_ascii=False, indent=2)}]
        }
    
    return {
        "content": [{"type": "text", "text": f"Unknown tool: {name}"}],
        "isError": True,
    }


if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("PORT", "8788"))
    print(f"🔮 东方术数 MCP Server v0.2.0 启动在 http://localhost:{port}")
    print(f"   SSE endpoint: http://localhost:{port}/sse")
    print(f"   免费额度: {FREE_DAILY_LIMIT} 次/天（匿名用户）")
    uvicorn.run(app, host="0.0.0.0", port=port)
