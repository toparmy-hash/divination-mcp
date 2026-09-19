"""
六壬解读模块 v0.1 — 灵屹术数 MCP
基于课式、三传、六亲、天将、旬空做结构化解读
输出：吉凶 + 方向 + 3条关键建议
"""
import json
import sys
import os
sys.path.insert(0, "/Users/liuyang/.openclaw/workspace/projects/divination-mcp")
from liuren import liuren as calc, DIZHI, TIANGAN, WUXING_MAP, GAN_WUXING, WX, LIUQIN_NAMES, TIANGAN

# 方位映射（地支→方位）
DIZHI_FANGWEI = {
    '子': '正北', '丑': '东北偏北', '寅': '东北偏东',
    '卯': '正东', '辰': '东南偏东', '巳': '东南偏南',
    '午': '正南', '未': '西南偏南', '申': '西南偏西',
    '酉': '正西', '戌': '西北偏西', '亥': '西北偏北',
}

# 十二时辰
DIZHI_SHICHEN = {
    '子': '23-1时', '丑': '1-3时', '寅': '3-5时', '卯': '5-7时',
    '辰': '7-9时', '巳': '9-11时', '午': '11-13时', '未': '13-15时',
    '申': '15-17时', '酉': '17-19时', '戌': '19-21时', '亥': '21-23时',
}

def interpret(pan, question=""):
    """解读六壬课盘，返回结构化结果"""
    result = {
        "overall": "",       # 总断：大吉/吉/平/凶/大凶
        "direction": "",     # 有利方向
        "timing": "",        # 有利时机
        "key_points": [],    # 3条关键建议
        "detail": "",        # 详细解读
        "elements": {},      # 关键要素
    }

    # 提取关键要素
    chu = pan['三传明细']['初传']
    zhong = pan['三传明细']['中传']
    mo = pan['三传明细']['末传']
    keshi = pan['三传']['课式']
    xun_kong = pan['旬空']
    ri_gan_wx = pan['日干五行']

    # ===== 1. 吉凶判断 =====
    score = 0  # 正为吉，负为凶

    # 课式吉凶
    keshi_jixiong = {
        '元首': 2, '重审': 1, '知一': 1, '伏吟': -1, '反吟': -2,
        '八专': 0, '别责': 0, '三光': 3, '三阳': 2,
        '龙战': -1, '斫轮': 2, '铸印': 2, '轩盖': 2,
        '六纯': -2, '乱首': -2, '悖戾': -1,
    }
    score += keshi_jixiong.get(keshi, 0)
    result['elements']['课式'] = f"{keshi}（{keshi_jixiong.get(keshi, 0):+d}分）"

    # 初传吉凶（发端）
    chu_liuqin = chu['六亲']
    liuqin_score = {
        '官鬼': -2, '妻财': 1, '子孙': 2, '父母': 0, '兄弟': -1
    }
    score += liuqin_score.get(chu_liuqin, 0)
    result['elements']['初传'] = f"{chu['传支']}落{chu['地盘']} 乘{chu['天将']} {chu_liuqin}"

    # 末传吉凶（结果）
    mo_liuqin = mo['六亲']
    score += liuqin_score.get(mo_liuqin, 0) * 2  # 末传权重更大
    result['elements']['末传'] = f"{mo['传支']}落{mo['地盘']} 乘{mo['天将']} {mo_liuqin}"

    # 旬空影响
    if chu['旬空']:
        score -= 2
        result['elements']['初传旬空'] = "发用空亡，事多虚声"
    if mo['旬空']:
        score -= 3
        result['elements']['末传旬空'] = "结局空亡，有头无尾"
    if not chu['旬空'] and not mo['旬空']:
        score += 1
        result['elements']['三传不空'] = "始终充实，事有实落"

    # 天将吉否（初传+末传）
    tianjiang_ji = ['贵人', '青龙', '六合', '太常', '天后']
    tianjiang_xiong = ['螣蛇', '朱雀', '勾陈', '白虎', '玄武', '天空']
    if chu['天将'] in tianjiang_ji:
        score += 1
    if chu['天将'] in tianjiang_xiong:
        score -= 1
    if mo['天将'] in tianjiang_ji:
        score += 2
    if mo['天将'] in tianjiang_xiong:
        score -= 2

    # 总分映射
    if score >= 5:
        result['overall'] = '大吉'
    elif score >= 2:
        result['overall'] = '吉'
    elif score >= -1:
        result['overall'] = '平'
    elif score >= -4:
        result['overall'] = '凶'
    else:
        result['overall'] = '大凶'

    result['elements']['综合得分'] = f"{score:+d}分"

    # ===== 2. 有利方向 =====
    # 找三传中最吉的地支对应的方位
    best_branch = None
    best_score = -99

    for chuan_info in [chu, zhong, mo]:
        s = liuqin_score.get(chuan_info['六亲'], 0)
        if chuan_info['天将'] in tianjiang_ji:
            s += 1
        if chuan_info['旬空']:
            s -= 3
        if s > best_score and not chuan_info['旬空']:
            best_score = s
            best_branch = chuan_info['传支']

    if best_branch:
        result['direction'] = DIZHI_FANGWEI.get(best_branch, '不确定') + '（' + best_branch + '方）'
    else:
        result['direction'] = '宜守不宜动，暂无利方'

    # ===== 3. 时机判断 =====
    # 找最吉的地支对应的时辰
    all_palaces = pan['天地盘']
    best_time = None
    best_time_score = -99
    for g in all_palaces:
        s = liuqin_score.get(g['六亲'], 0)
        if g['天将'] in tianjiang_ji:
            s += 1
        if g['旬空']:
            continue
        if s > best_time_score:
            best_time_score = s
            best_time = g['宫']

    if best_time:
        result['timing'] = f"{DIZHI_SHICHEN.get(best_time, '?')}（{best_time}时）最有力"
    else:
        result['timing'] = "近期皆不宜，静待时机"

    # ===== 4. 三条关键建议 =====
    tips = []

    # 基于初传
    if chu['旬空']:
        tips.append("发用空亡：此事开头容易虚张声势，不要被表面声势迷惑，看实不看名。")
    elif chu['六亲'] == '官鬼':
        tips.append("初传官鬼：此事阻力大、压力重，强行推进反受其害，先化解阻力再动手。")
    elif chu['六亲'] == '子孙':
        tips.append("初传子孙：福神发用，事有生机，但不可急躁，让子弹飞一会儿。")
    elif chu['六亲'] == '妻财':
        tips.append("初传妻财：财星发动，利益相关之事有戏，但须防因小失大。")
    elif chu['六亲'] == '父母':
        tips.append("初传父母：文书、信息、长辈相关，要靠文件和规则，不靠人情。")
    elif chu['六亲'] == '兄弟':
        tips.append("初传兄弟：竞争、分利、口舌，与人合作要先讲清楚利益分配。")

    # 基于末传（结局）
    if mo['旬空']:
        tips.append("末传空亡：结局容易落空，不要投入太多，抱「试试看」心态即可。")
    elif mo['六亲'] == '子孙':
        tips.append("末传子孙：结局无忧，能消灾解厄，过程再难最终都能落地。")
    elif mo['六亲'] == '官鬼':
        tips.append("末传官鬼：结尾多灾，要留后手，不要把所有筹码都压上去。")
    elif mo['六亲'] == '妻财':
        tips.append("末传妻财：最终有利可得，但得之不易，要有持久战准备。")

    # 基于课式
    if keshi == '反吟':
        tips.append("反吟课：事情反复、变化快，不要一次下重注，分批行动，留回转余地。")
    elif keshi == '伏吟':
        tips.append("伏吟课：事情停滞、动弹不得，急也没用，宜守宜等，内省不妄动。")
    elif keshi == '元首':
        tips.append("元首课：正气之象，顺势而为即可，不要耍小聪明。")
    elif keshi == '重审':
        tips.append("重审课：需再三思量、反复求证，第一直觉往往不准，多问几个为什么。")

    # 确保至少3条，不够就补通用建议
    general_tips = [
        "此事不可独断，找信任的人商量一下再决定。",
        "注意文书和合同细节，口头承诺不算数。",
        "健康方面注意作息，思虑过度伤脾。",
        "不要在情绪激动时做决定，睡一觉再说。",
    ]
    for tip in general_tips:
        if len(tips) >= 3:
            break
        tips.append(tip)

    result['key_points'] = tips[:3]

    # ===== 5. 详细解读 =====
    result['detail'] = (
        f"课式：{keshi}。"
        f"初传{chu['传支']}乘{chu['天将']}为{chu['六亲']}，"
        f"中传{zhong['传支']}乘{zhong['天将']}为{zhong['六亲']}，"
        f"末传{mo['传支']}乘{mo['天将']}为{mo['六亲']}。"
        f"旬空：{'、'.join(xun_kong)}。"
        f"日干为{pan['日干五行']}。"
    )

    return result


if __name__ == '__main__':
    from datetime import datetime
    now = datetime.now()
    pan = calc(now.year, now.month, now.day, now.hour)
    question = sys.argv[1] if len(sys.argv) > 1 else ""
    result = interpret(pan, question)
    print(json.dumps(result, ensure_ascii=False, indent=2))
