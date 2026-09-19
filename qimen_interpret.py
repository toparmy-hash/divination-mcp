"""
奇门遁甲解读模块 v0.1 — 灵屹术数 MCP
基于阴盘奇门盘面（读盘大师格式）做结构化解读
输出：吉凶 + 方向 + 时机 + 3条关键建议
"""
import json
import sys
import subprocess

# 九宫方位映射
GONG_FANGWEI = {
    '1': '正北', '2': '西南', '3': '正东', '4': '东南',
    '6': '西北', '7': '正西', '8': '东北', '9': '正南',
    '5': '中宫',
}

# 八门吉凶（基础分）
MEN_JIXIONG = {
    '开门': 3, '休门': 2, '生门': 3,
    '伤门': -2, '杜门': -1, '景门': 1,
    '死门': -3, '惊门': -2,
}

# 九星吉凶
XING_JIXIONG = {
    '天心': 2, '天蓬': -1, '天任': 1, '天冲': 1,
    '天辅': 2, '天英': 0, '天芮': -2, '天柱': -1, '天禽': 1,
}

# 八神吉凶
SHEN_JIXIONG = {
    '值符': 3, '螣蛇': -1, '太阴': 1, '六合': 2,
    '白虎': -2, '玄武': -2, '九地': 0, '九天': 1,
}

# 十天干吉凶（基础）
GAN_JIXIONG = {
    '甲': 2, '乙': 1, '丙': 1, '丁': 2,
    '戊': 1, '己': 0, '庚': -2, '辛': -1, '壬': 0, '癸': -1,
}

# 五行生克
WUXING_SHENG = {
    '金': '水', '水': '木', '木': '火', '火': '土', '土': '金'
}
WUXING_KE = {
    '金': '木', '木': '土', '土': '水', '水': '火', '火': '金'
}

# 九宫五行
GONG_WUXING = {
    '1': '水', '2': '土', '3': '木', '4': '木',
    '5': '土', '6': '金', '7': '金', '8': '土', '9': '火',
}

# 天干五行
GAN_WUXING = {
    '甲': '木', '乙': '木', '丙': '火', '丁': '火',
    '戊': '土', '己': '土', '庚': '金', '辛': '金',
    '壬': '水', '癸': '水',
}

# 八门五行
MEN_WUXING = {
    '开门': '金', '休门': '水', '生门': '土',
    '伤门': '木', '杜门': '木', '景门': '火',
    '死门': '土', '惊门': '金',
}

# 九星五行
XING_WUXING = {
    '天心': '金', '天蓬': '水', '天任': '土', '天冲': '木',
    '天辅': '木', '天英': '火', '天芮': '土', '天柱': '金', '天禽': '土',
}


def shengke(a_wx, b_wx):
    """判断a对b的生克关系：a生b返回1，a克b返回-1，b生a返回-0.5，b克a返回0.5，比和返回0"""
    if a_wx == b_wx:
        return 0  # 比和
    if WUXING_SHENG.get(a_wx) == b_wx:
        return 1  # a生b
    if WUXING_KE.get(a_wx) == b_wx:
        return -1  # a克b
    if WUXING_SHENG.get(b_wx) == a_wx:
        return -0.5  # b生a（a泄气）
    if WUXING_KE.get(b_wx) == a_wx:
        return 0.5  # b克a（a受克，但这是对方克过来，对a是凶）
    return 0


def gong_score(gong_info, gong_key):
    """计算单宫综合得分"""
    score = 0
    details = []

    # 八门
    men = gong_info.get('八门', '')
    men_s = MEN_JIXIONG.get(men, 0)
    score += men_s
    if men_s != 0:
        details.append(f"{men}（{men_s:+d}）")

    # 九星
    xing = gong_info.get('九星', '')
    xing_s = XING_JIXIONG.get(xing, 0)
    score += xing_s
    if xing_s != 0:
        details.append(f"{xing}（{xing_s:+d}）")

    # 八神
    shen = gong_info.get('八神', '')
    shen_s = SHEN_JIXIONG.get(shen, 0)
    score += shen_s
    if shen_s != 0:
        details.append(f"{shen}（{shen_s:+d}）")

    # 天盘干
    tp = gong_info.get('天盘', '')
    tp_s = GAN_JIXIONG.get(tp, 0)
    score += tp_s

    # 门宫生克
    gong_wx = GONG_WUXING.get(gong_key, '土')
    men_wx = MEN_WUXING.get(men, '')
    if men_wx:
        sk = shengke(men_wx, gong_wx)
        if sk == 1:  # 门生宫
            score += 1
            details.append("门生宫（+1）")
        elif sk == -1:  # 门克宫
            score -= 2
            details.append("门克宫（-2）")
        elif sk == -0.5:  # 宫生门（泄气）
            score -= 0.5
        elif sk == 0.5:  # 宫克门
            score += 0.5

    # 星宫生克
    xing_wx = XING_WUXING.get(xing, '')
    if xing_wx:
        sk = shengke(xing_wx, gong_wx)
        if sk == 1:  # 星生宫
            score += 0.5
        elif sk == -1:  # 星克宫
            score -= 1
            details.append("星克宫（-1）")

    # 空亡
    if '空亡' in gong_info.get('标记', []):
        score -= 3
        details.append("空亡（-3）")

    # 马星
    if '马星' in gong_info.get('标记', []):
        score += 0.5  # 马星主动，中性偏吉

    return score, details


def interpret(pan, question=""):
    """解读奇门盘，返回结构化结果"""
    result = {
        "overall": "",       # 总断：大吉/吉/平/凶/大凶
        "direction": "",     # 有利方向
        "timing": "",        # 有利时机
        "key_points": [],    # 3条关键建议
        "detail": "",        # 详细解读
        "elements": {},      # 关键要素
    }

    jiugong = pan['九宫']
    zhi_fu_gong = str(pan.get('值符落宫', ''))
    shi_gan_gong = str(pan.get('时干解读宫', pan.get('时干宫', '')))
    dunju = pan.get('遁局', '')
    xun_kong = pan.get('空亡', [])
    ma_xing = pan.get('马星', None)

    result['elements']['遁局'] = dunju
    result['elements']['值符落宫'] = zhi_fu_gong + '宫'
    result['elements']['时干宫'] = shi_gan_gong + '宫'
    if xun_kong:
        result['elements']['空亡'] = '、'.join(str(x) + '宫' for x in xun_kong)
    if ma_xing is not None:
        result['elements']['马星'] = str(ma_xing) + '宫'

    # ===== 1. 吉凶判断 =====
    total_score = 0

    # 时干宫得分（主事体，权重最高）
    if shi_gan_gong and shi_gan_gong in jiugong:
        s, details = gong_score(jiugong[shi_gan_gong], shi_gan_gong)
        total_score += s * 2  # 时干宫权重×2
        result['elements']['时干宫得分'] = f"{s:+.1f}×2"
        result['elements']['时干宫细节'] = '、'.join(details) if details else '平稳'

    # 值符宫得分（主贵人/助力）
    if zhi_fu_gong and zhi_fu_gong in jiugong:
        s, details = gong_score(jiugong[zhi_fu_gong], zhi_fu_gong)
        total_score += s * 1.5
        result['elements']['值符宫得分'] = f"{s:+.1f}×1.5"
        result['elements']['值符宫细节'] = '、'.join(details) if details else '平稳'

    # 各宫平均得分
    all_scores = []
    best_gong = None
    best_score = -99
    worst_gong = None
    worst_score = 99

    for gk, gi in jiugong.items():
        s, _ = gong_score(gi, gk)
        all_scores.append(s)
        if s > best_score:
            best_score = s
            best_gong = gk
        if s < worst_score:
            worst_score = s
            worst_gong = gk

    avg_score = sum(all_scores) / len(all_scores) if all_scores else 0
    total_score += avg_score * 0.5  # 整体氛围

    result['elements']['全局均值'] = f"{avg_score:+.1f}×0.5"
    result['elements']['最吉宫'] = f"{best_gong}宫（{best_score:+.1f}）"
    result['elements']['最凶宫'] = f"{worst_gong}宫（{worst_score:+.1f}）"

    # 值符宫生时干宫？（贵人帮不帮）
    if zhi_fu_gong and shi_gan_gong and zhi_fu_gong in jiugong and shi_gan_gong in jiugong:
        zf_wx = GONG_WUXING.get(zhi_fu_gong, '')
        sg_wx = GONG_WUXING.get(shi_gan_gong, '')
        if zf_wx and sg_wx:
            sk = shengke(zf_wx, sg_wx)
            if sk == 1:  # 值符生时干
                total_score += 2
                result['elements']['值符生时干'] = '贵人相助（+2）'
            elif sk == -1:  # 值符克时干
                total_score -= 2
                result['elements']['值符克时干'] = '受制于人（-2）'
            elif sk == 0.5:  # 时干克值符
                total_score -= 1
                result['elements']['时干克值符'] = '以下犯上（-1）'

    # 总分映射
    if total_score >= 6:
        result['overall'] = '大吉'
    elif total_score >= 2:
        result['overall'] = '吉'
    elif total_score >= -2:
        result['overall'] = '平'
    elif total_score >= -6:
        result['overall'] = '凶'
    else:
        result['overall'] = '大凶'

    result['elements']['综合得分'] = f"{total_score:+.1f}分"

    # ===== 2. 有利方向 =====
    if best_gong and best_score > 0:
        direction = GONG_FANGWEI.get(best_gong, '不确定')
        result['direction'] = f"{direction}（{best_gong}宫）最有利"
    else:
        result['direction'] = '全局皆弱，宜守不宜动，暂无利方'

    # ===== 3. 时机判断 =====
    # 马星主动，空亡主虚
    if ma_xing is not None and ma_xing not in [xk for xk in xun_kong]:
        ma_gong = str(ma_xing)
        result['timing'] = f"马星在{ma_gong}宫，事有动象，近期3-5日内可见变化"
    elif xun_kong:
        result['timing'] = f"空亡在{'、'.join(str(x)+'宫' for x in xun_kong)}，事多虚声，出空后（约10天）方有实落"
    else:
        result['timing'] = "格局平稳，快慢由人，主动推进则快，静待则迟"

    # ===== 4. 三条关键建议 =====
    tips = []

    # 基于时干宫八门
    if shi_gan_gong and shi_gan_gong in jiugong:
        men = jiugong[shi_gan_gong].get('八门', '')
        if men == '开门':
            tips.append("时干逢开门：此事宜公开、宜主动、宜扩大，藏着掖着反而坏事。")
        elif men == '休门':
            tips.append("时干逢休门：宜休整、宜谈判、宜软着陆，硬攻反而不利。")
        elif men == '生门':
            tips.append("时干逢生门：财运、生机之象，跟钱和增长相关的事有利。")
        elif men == '伤门':
            tips.append("时干逢伤门：防损伤、防争执，动手之前先想清楚代价。")
        elif men == '杜门':
            tips.append("时干逢杜门：阻塞不通，硬闯没用，另寻他路或暂避锋芒。")
        elif men == '景门':
            tips.append("时干逢景门：文书、信息、宣传有利，但防口舌是非。")
        elif men == '死门':
            tips.append("时干逢死门：死气沉沉，不宜新动，能停就停，不能停也要减量。")
        elif men == '惊门':
            tips.append("时干逢惊门：口舌是非多，少说多做，别被谣言牵着走。")

    # 基于值符八神
    if zhi_fu_gong and zhi_fu_gong in jiugong:
        shen = jiugong[zhi_fu_gong].get('八神', '')
        if shen == '值符':
            tips.append("值符当位：有贵人、有规则、有靠山，按规矩来就没错。")
        elif shen == '螣蛇':
            tips.append("螣蛇为患：事多虚诈、变化莫测，不要轻信表象，多留个心眼。")
        elif shen == '太阴':
            tips.append("太阴庇佑：宜暗中筹划、宜密谋，不宜声张，默默做就好。")
        elif shen == '六合':
            tips.append("六合合和：宜合作、宜谈判、宜多方联合，单打独斗不如借力。")
        elif shen == '白虎':
            tips.append("白虎当道：防突发事件、防冲突，做好最坏准备，不要赌运气。")
        elif shen == '玄武':
            tips.append("玄武为贼：防被骗、防丢失、防小人，钱财往来务必留凭证。")
        elif shen == '九地':
            tips.append("九地为牢：宜守不宜攻，根基稳固再动，不要好高骛远。")
        elif shen == '九天':
            tips.append("九天之上：宜扬不宜藏，主动出击、扩大声势有利。")

    # 基于空亡和马星
    if xun_kong and len(xun_kong) > 0:
        tips.append(f"空亡在{'、'.join(str(x)+'宫' for x in xun_kong)}：相关之事多虚少实，不要过早投入，等出空再定。")
    if ma_xing is not None:
        tips.append(f"马星动于{ma_xing}宫：事有变动，不要固守成规，跟着变化调整。")

    # 基于全局判断
    if result['overall'] in ['大凶', '凶']:
        tips.append("格局不吉，不要硬上，能拖就拖，能减就减，保全为上。")
    elif result['overall'] == '大吉':
        tips.append("格局大顺，看准就上，不要犹豫，错过时机反而可惜。")

    # 确保至少3条
    general_tips = [
        "凡事留三分余地，话不说满，事不做绝。",
        "注意身体，思虑过重伤脾胃，该休息时要休息。",
        "不要在深夜做重要决定，睡一觉，答案会更清楚。",
    ]
    for tip in general_tips:
        if len(tips) >= 3:
            break
        tips.append(tip)

    result['key_points'] = tips[:3]

    # ===== 5. 详细解读 =====
    sg_info = jiugong.get(shi_gan_gong, {})
    zf_info = jiugong.get(zhi_fu_gong, {})
    result['detail'] = (
        f"{dunju}。"
        f"时干在{shi_gan_gong}宫：{sg_info.get('八门','')}、{sg_info.get('九星','')}、{sg_info.get('八神','')}，"
        f"天盘{sg_info.get('天盘','')}地盘{sg_info.get('地盘','')}。"
        f"值符在{zhi_fu_gong}宫：{zf_info.get('八门','')}、{zf_info.get('九星','')}、{zf_info.get('八神','')}。"
        f"空亡：{'、'.join(str(x)+'宫' for x in xun_kong) if xun_kong else '无'}。"
        f"马星：{str(ma_xing)+'宫' if ma_xing is not None else '无'}。"
    )

    return result


def get_qimen_pan(time_str=None):
    """调用读盘大师获取奇门盘"""
    cmd = ['python3', '/Users/liuyang/.hermes/scripts/读盘大师.py']
    if time_str:
        cmd += ['--time', time_str]
    else:
        cmd += ['--now']
    
    result = subprocess.run(cmd, capture_output=True, text=True, timeout=15)
    if result.returncode != 0:
        raise RuntimeError(f"读盘大师执行失败: {result.stderr}")
    return json.loads(result.stdout)


if __name__ == '__main__':
    question = sys.argv[1] if len(sys.argv) > 1 else ""
    time_str = sys.argv[2] if len(sys.argv) > 2 else None
    pan = get_qimen_pan(time_str)
    result = interpret(pan, question)
    print(json.dumps(result, ensure_ascii=False, indent=2))
