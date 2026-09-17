#!/usr/bin/env python3
"""
术数 MCP 服务 - MVP
提供紫微斗数、奇门遁甲、易经起卦等 API
"""
import json
import subprocess
import sys
import os
from datetime import datetime
from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional

app = FastAPI(title="东方术数 MCP 服务", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

ZIWEI_SCRIPT = "/Users/liuyang/.openclaw/workspace/skills/ziwei-doushu/scripts/ziwei_chart.py"

# ========== 数据模型 ==========
class ZiweiRequest(BaseModel):
    date: str  # YYYY-MM-DD
    time: str  # HH:MM
    gender: str  # male/female
    timezone: Optional[str] = "Asia/Shanghai"
    longitude: Optional[float] = 120.0

class IChingRequest(BaseModel):
    question: str
    method: Optional[str] = "random"  # random / coins

class DailyRequest(BaseModel):
    date: Optional[str] = None

# ========== 紫微斗数 ==========
@app.post("/api/ziwei/chart")
def ziwei_chart(req: ZiweiRequest):
    """紫微斗数排盘"""
    try:
        cmd = [
            sys.executable, ZIWEI_SCRIPT,
            "--date", req.date,
            "--time", req.time,
            "--gender", req.gender,
            "--timezone", req.timezone,
            "--longitude", str(req.longitude),
            "--format", "json",
            "--template", "lite",
            "--engine", "py",
        ]
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
        if result.returncode != 0:
            raise HTTPException(status_code=500, detail=result.stderr[:200])
        
        data = json.loads(result.stdout)
        zw = data.get("ziwei", data)
        
        # 精简输出，只保留核心信息
        palaces = []
        for p in zw.get("palaces", []):
            major_stars = [s.get("name", "") for s in p.get("major_stars", [])]
            palaces.append({
                "name": p.get("name", ""),
                "stem_branch": f"{p.get('stem','')}{p.get('branch','')}",
                "major_stars": major_stars,
            })
        
        # 生年四化
        mutagen = []
        for m in zw.get("birth_mutagen", []):
            mutagen.append({
                "star": m.get("star", ""),
                "mutagen": m.get("mutagen", ""),
                "palace": m.get("palace", ""),
            })
        
        return {
            "success": True,
            "service": "紫微斗数排盘",
            "basic_info": {
                "date": req.date,
                "time": req.time,
                "gender": req.gender,
                "five_elements_class": zw.get("five_elements_class", ""),
                "ming_palace": zw.get("ming", {}).get("name", ""),
                "ming_stem_branch": f"{zw.get('ming',{}).get('stem','')}{zw.get('ming',{}).get('branch','')}",
                "body_palace": zw.get("body", {}).get("name", ""),
            },
            "twelve_palaces": palaces,
            "birth_mutagen": mutagen,
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e)[:200])

# ========== 易经起卦 ==========
@app.post("/api/iching/gua")
def iching_gua(req: IChingRequest):
    """易经起卦（随机数模拟铜钱法）"""
    import random
    
    # 三枚铜钱起六爻
    lines = []
    for _ in range(6):
        coins = [random.choice([2, 3]) for _ in range(3)]  # 2=阴, 3=阳
        total = sum(coins)
        # 6=老阴(变), 7=少阳(不变), 8=少阴(不变), 9=老阳(变)
        lines.append(total)
    
    # 从下往上排
    lines.reverse()
    
    # 八卦对应表
    # 八卦（从下往上数三爻，7=阳，8=阴）
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
    
    # 取卦象用本质阴阳：6=老阴=阴(8), 9=老阳=阳(7)
    def yao_value(l):
        if l in [6, 8]: return 8  # 阴
        if l in [7, 9]: return 7  # 阳
        return l
    lower_tri = tuple(yao_value(l) for l in lines[:3])  # 下卦
    upper_tri = tuple(yao_value(l) for l in lines[3:])  # 上卦
    
    lower_name, lower_sym, lower_ele = trigrams.get(lower_tri, ("?", "?", "?"))
    upper_name, upper_sym, upper_ele = trigrams.get(upper_tri, ("?", "?", "?"))
    
    # 变爻
    changing_lines = [i+1 for i, l in enumerate(lines) if l in [6, 9]]
    
    # 64卦名（简化版，只给上下卦组合名）
    hexagram_name = f"{upper_name}{lower_name}"
    
    return {
        "success": True,
        "service": "易经起卦",
        "question": req.question,
        "hexagram": {
            "name": hexagram_name,
            "upper": {"name": upper_name, "symbol": upper_sym, "element": upper_ele},
            "lower": {"name": lower_name, "symbol": lower_sym, "element": lower_ele},
        },
        "lines": [
            {"position": i+1, "type": "老阴(变)" if l==6 else "少阳" if l==7 else "少阴" if l==8 else "老阳(变)", "value": l}
            for i, l in enumerate(lines)
        ],
        "changing_lines": changing_lines,
        "note": "此为起卦结果，解读需结合卦辞爻辞具体分析。如需深度解读请使用高级服务。",
    }

# ========== 今日宜忌 ==========
@app.get("/api/daily")
@app.post("/api/daily")
# ========== 大六壬 ==========
class LiurenRequest(BaseModel):
    date: str  # YYYY-MM-DD
    hour: int  # 时辰（0-23）
    question: Optional[str] = ""


@app.post("/api/liuren/chart")
def liuren_chart(req: LiurenRequest):
    """大六壬起盘"""
    try:
        import subprocess
        from datetime import datetime

        dt = datetime.strptime(req.date, "%Y-%m-%d")
        cmd = [
            sys.executable,
            os.path.join(os.path.dirname(__file__), "liuren.py"),
            str(dt.year), str(dt.month), str(dt.day),
            str(req.hour),
            "--json",
        ]
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=30,
                              cwd=os.path.dirname(__file__))
        if result.returncode != 0:
            raise HTTPException(status_code=500, detail=result.stderr[:200])

        data = json.loads(result.stdout)

        return {
            "success": True,
            "service": "大六壬起盘",
            "question": req.question,
            "time": data.get("时间", ""),
            "sizhu": data.get("四柱", {}),
            "yuejiang": data.get("月将", ""),
            "zhanshi": data.get("占时", ""),
            "xunkong": data.get("旬空", []),
            "tiandipan": data.get("天地盘", []),
            "sanke": data.get("三传", []),
            "sike": data.get("四课", []),
            "note": "此为起盘结果，深度解读需结合三传四课、六亲、神将分析。",
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e)[:200])


def daily_almanac(req: DailyRequest = None, request: Request = None):
    """今日黄历宜忌（天干地支版）"""
    from datetime import date as date_obj
    
    if req and req.date:
        d = datetime.strptime(req.date, "%Y-%m-%d").date()
    else:
        d = date_obj.today()
    
    # 计算日干支（简化版，用已知基准日推算）
    # 2000-01-01 是 庚辰日
    stems = ["甲", "乙", "丙", "丁", "戊", "己", "庚", "辛", "壬", "癸"]
    branches = ["子", "丑", "寅", "卯", "辰", "巳", "午", "未", "申", "酉", "戌", "亥"]
    
    base = date_obj(2000, 1, 1)
    delta = (d - base).days
    stem_idx = (delta + 6) % 10  # 庚=6
    branch_idx = (delta + 0) % 12  # 辰=4... 调整一下
    
    # 更准确的：2000年1月1日是庚辰日
    # 庚是第7个(索引6)，辰是第5个(索引4)
    stem_idx = (6 + delta) % 10
    branch_idx = (4 + delta) % 12
    
    day_ganzhi = f"{stems[stem_idx]}{branches[branch_idx]}"
    
    # 五行
    wuxing_stem = {"甲":"木","乙":"木","丙":"火","丁":"火","戊":"土","己":"土","庚":"金","辛":"金","壬":"水","癸":"水"}
    wuxing_branch = {"子":"水","丑":"土","寅":"木","卯":"木","辰":"土","巳":"火","午":"火","未":"土","申":"金","酉":"金","戌":"土","亥":"水"}
    
    # 简单宜忌（根据日支冲合）
    yi = ["祭祀", "祈福", "求嗣"]
    ji = ["动土", "破土"]
    
    # 根据不同日支调整
    zhi = branches[branch_idx]
    if zhi in ["子", "午"]:
        yi = ["祭祀", "祈福", "出行", "见贵"]
        ji = ["嫁娶", "动土"]
    elif zhi in ["卯", "酉"]:
        yi = ["交易", "立券", "纳财", "开市"]
        ji = ["搬家", "远行"]
    elif zhi in ["寅", "申"]:
        yi = ["求医", "治病", "解除"]
        ji = ["嫁娶", "搬家"]
    elif zhi in ["巳", "亥"]:
        yi = ["学习", "考试", "求职", "见贵"]
        ji = ["投资", "冒险"]
    elif zhi in ["辰", "戌", "丑", "未"]:
        yi = ["修造", "动土", "安葬", "奠基"]
        ji = ["嫁娶", "远行"]
    
    return {
        "success": True,
        "date": d.isoformat(),
        "weekday": ["周一","周二","周三","周四","周五","周六","周日"][d.weekday()],
        "ganzhi": day_ganzhi,
        "wuxing": f"{wuxing_stem[stems[stem_idx]]}{wuxing_branch[branches[branch_idx]]}",
        "yi": yi,
        "ji": ji,
        "note": "此为简化版黄历，仅供参考。详细择日需结合个人命盘。",
    }

# ========== 健康检查 ==========
@app.get("/api/health")
def health():
    return {"status": "ok", "service": "东方术数 MCP 服务", "version": "0.1.0"}

@app.get("/")
def root():
    return {
        "name": "东方术数 MCP 服务",
        "version": "0.1.0",
        "endpoints": {
            "POST /api/ziwei/chart": "紫微斗数排盘",
            "POST /api/iching/gua": "易经起卦",
            "POST /api/liuren/chart": "大六壬起盘",
            "GET/POST /api/daily": "今日宜忌",
            "GET /api/health": "健康检查",
        },
        "pricing": {
            "紫微排盘": "$0.5 USDC / 次",
            "易经起卦": "$0.3 USDC / 次",
            "大六壬起盘": "$0.5 USDC / 次",
            "今日宜忌": "免费",
        }
    }

if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("PORT", "8787"))
    print(f"🌿 东方术数 MCP 服务启动在 http://localhost:{port}")
    uvicorn.run(app, host="0.0.0.0", port=port)
