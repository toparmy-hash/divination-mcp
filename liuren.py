#!/usr/bin/env python3
"""
大六壬起盘工具 v2.0 — 小壬·灵屹专用
用法: python3 liuren.py [年 月 日 时] [--json]
无参数默认取当前北京时间。
"""

import sys, json
from datetime import datetime, timedelta

# ==================== 基础数据 ====================
DIZHI = ['子','丑','寅','卯','辰','巳','午','未','申','酉','戌','亥']
TIANGAN = ['甲','乙','丙','丁','戊','己','庚','辛','壬','癸']
DIZHI_NUM = {d:i for i,d in enumerate(DIZHI)}
TIANGAN_NUM = {t:i for i,t in enumerate(TIANGAN)}

WUXING_MAP = {
    '寅':'木','卯':'木','辰':'土','巳':'火','午':'火',
    '未':'土','申':'金','酉':'金','戌':'土','亥':'水','子':'水','丑':'土'
}
GAN_WUXING = {'甲':'木','乙':'木','丙':'火','丁':'火','戊':'土','己':'土','庚':'金','辛':'金','壬':'水','癸':'水'}

GAN_JIGONG = {'甲':'寅','乙':'辰','丙':'巳','丁':'未','戊':'巳','己':'未','庚':'申','辛':'戌','壬':'亥','癸':'丑'}

TIANJIANG = ['贵人','螣蛇','朱雀','六合','勾陈','青龙','天空','白虎','太常','玄武','太阴','天后']
TIANJIANG_SHUN = ['贵人','螣蛇','朱雀','六合','勾陈','青龙','天空','白虎','太常','玄武','太阴','天后']
TIANJIANG_NI   = ['贵人','天后','太阴','玄武','太常','白虎','天空','青龙','勾陈','六合','朱雀','螣蛇']

GUIREN_MAP = {
    '甲':('丑','未'),'戊':('丑','未'),'庚':('丑','未'),
    '乙':('子','申'),'己':('子','申'),
    '丙':('亥','酉'),'丁':('亥','酉'),
    '壬':('卯','巳'),'癸':('卯','巳'),
    '辛':('寅','午')
}

WX = {
    '木':{'生':'火','克':'土','被生':'水','被克':'金'},
    '火':{'生':'土','克':'金','被生':'木','被克':'水'},
    '土':{'生':'金','克':'水','被生':'火','被克':'木'},
    '金':{'生':'水','克':'木','被生':'土','被克':'火'},
    '水':{'生':'木','克':'火','被生':'金','被克':'土'}
}

LIUQIN_NAMES = {'克':'官鬼','被克':'妻财','生':'子孙','被生':'父母','同':'兄弟'}

JIEQI_2026_2027 = [
    ('2026-01-05','小寒'),('2026-01-20','大寒'),('2026-02-04','立春'),('2026-02-19','雨水'),
    ('2026-03-05','惊蛰'),('2026-03-20','春分'),('2026-04-05','清明'),('2026-04-20','谷雨'),
    ('2026-05-05','立夏'),('2026-05-21','小满'),('2026-06-05','芒种'),('2026-06-21','夏至'),
    ('2026-07-07','小暑'),('2026-07-23','大暑'),('2026-08-07','立秋'),('2026-08-23','处暑'),
    ('2026-09-07','白露'),('2026-09-23','秋分'),('2026-10-08','寒露'),('2026-10-23','霜降'),
    ('2026-11-07','立冬'),('2026-11-22','小雪'),('2026-12-07','大雪'),('2026-12-21','冬至'),
    ('2027-01-05','小寒'),('2027-01-20','大寒')
]

ZHONGQI_YUEJIANG = {
    '冬至':'丑','大寒':'子','雨水':'亥','春分':'戌',
    '谷雨':'酉','小满':'申','夏至':'未','大暑':'午',
    '处暑':'巳','秋分':'辰','霜降':'卯','小雪':'寅'
}

JIE_MONTH_BRANCH = {
    '立春':'寅','惊蛰':'卯','清明':'辰','立夏':'巳','芒种':'午','小暑':'未',
    '立秋':'申','白露':'酉','寒露':'戌','立冬':'亥','大雪':'子','小寒':'丑'
}

XING_NEXT = {
    '寅':'巳','巳':'申','申':'寅',
    '丑':'戌','戌':'未','未':'丑',
    '子':'卯','卯':'子',
    '辰':'辰','午':'午','酉':'酉','亥':'亥'
}

# 旬空
XUNKONG = {
    '甲子':'戌亥','甲戌':'申酉','甲申':'午未','甲午':'辰巳',
    '甲辰':'寅卯','甲寅':'子丑'
}

def get_xun_start(ri_gan, ri_zhi):
    """找到日干支所在的旬首"""
    zhi_idx = DIZHI_NUM[ri_zhi]
    gan_idx = TIANGAN_NUM[ri_gan]
    diff = (gan_idx - zhi_idx) % 10
    xun_idx = gan_idx - diff
    if xun_idx < 0:
        xun_idx += 10
    return TIANGAN[xun_idx], diff

def get_xun_kong(ri_gan, ri_zhi):
    """获取旬空的两个地支"""
    # 找旬首地支: 从日支往前找，找到天干=甲的那组
    zhi_idx = DIZHI_NUM[ri_zhi]
    gan_idx = TIANGAN_NUM[ri_gan]
    xun_start_zhi = (zhi_idx - ((gan_idx - 0) % 10)) % 12
    # 旬空 = 旬首地支往前两位
    kong1 = DIZHI[(xun_start_zhi - 1) % 12]
    kong2 = DIZHI[(xun_start_zhi - 2) % 12]
    return sorted([kong1, kong2], key=lambda d: DIZHI_NUM[d])

# ==================== 核心算法 ====================

def get_yue_jiang(month, day, year=2026):
    """根据公历月日查月将"""
    date_str = f"{year}-{month:02d}-{day:02d}"
    current = datetime.strptime(date_str, '%Y-%m-%d')
    
    for jq_date, jq_name in reversed(JIEQI_2026_2027):
        jq_dt = datetime.strptime(jq_date, '%Y-%m-%d')
        if jq_dt <= current and jq_name in ZHONGQI_YUEJIANG:
            return ZHONGQI_YUEJIANG[jq_name]
    return '丑'  # default 冬至后

def get_month_ganzhi(year, month, day):
    """按节令月与五虎遁计算月柱。"""
    current = datetime(year, month, day)
    month_branch = '丑'
    for jq_date, jq_name in reversed(JIEQI_2026_2027):
        jq_dt = datetime.strptime(jq_date, '%Y-%m-%d')
        if jq_dt <= current and jq_name in JIE_MONTH_BRANCH:
            month_branch = JIE_MONTH_BRANCH[jq_name]
            break

    year_gan_idx = (year - 4) % 10
    tiger_stem = {0:2, 5:2, 1:4, 6:4, 2:6, 7:6, 3:8, 8:8, 4:0, 9:0}[year_gan_idx]
    branch_offset = (DIZHI_NUM[month_branch] - DIZHI_NUM['寅']) % 12
    month_stem = TIANGAN[(tiger_stem + branch_offset) % 10]
    return month_stem + month_branch

def compute_ganzhi(year, month, day):
    """日干支（2026-01-01 = 乙亥，已验证：文墨天机+大师奇门交叉对照 2026-07-05=庚辰）"""
    base = datetime(2026, 1, 1)
    target = datetime(year, month, day)
    days = (target - base).days
    tg = (1 + days) % 10  # 乙
    dz = (11 + days) % 12  # 亥（非巳！2026-07-05已用文墨天机+大师奇门验证）
    return TIANGAN[tg], DIZHI[dz]

def get_shichen_ganzhi(ri_gan, hour):
    """五鼠遁取时干支"""
    if hour >= 23 or hour < 1:
        shichen = 0
    else:
        shichen = (hour + 1) // 2  # 0-23 → 0-11
    
    start = {'甲':0,'乙':2,'丙':4,'丁':6,'戊':8,'己':0,'庚':2,'辛':4,'壬':6,'癸':8}
    shi_gan = (start.get(ri_gan, 0) + shichen) % 10
    shi_zhi = shichen
    return TIANGAN[shi_gan], DIZHI[shi_zhi]

def tianpan(yue_jiang, shi_zhi):
    """月将加时：天盘从时支开始，顺时针排月将到亥"""
    result = [None]*12
    start = DIZHI_NUM[shi_zhi]
    yj = DIZHI_NUM[yue_jiang]
    for i in range(12):
        pos = (start + i) % 12
        tian = (yj + i) % 12
        result[pos] = DIZHI[tian]
    return result

def si_ke(ri_gan, ri_zhi, tianpan_zhi):
    """排四课"""
    jigong = GAN_JIGONG[ri_gan]
    jigong_idx = DIZHI_NUM[jigong]
    ri_zhi_idx = DIZHI_NUM[ri_zhi]
    
    k1x = jigong;   k1s = tianpan_zhi[jigong_idx]
    k2x = k1s;      k2s = tianpan_zhi[DIZHI_NUM[k2x]]
    k3x = ri_zhi;   k3s = tianpan_zhi[ri_zhi_idx]
    k4x = k3s;      k4s = tianpan_zhi[DIZHI_NUM[k4x]]
    
    return {1:(k1s,k1x), 2:(k2s,k2x), 3:(k3s,k3x), 4:(k4s,k4x)}

def check_ke_zei(shang, xia, ri_gan_wx):
    """检查贼克：下克上=贼，上克下=克"""
    xw = WUXING_MAP[xia]; sw = WUXING_MAP[shang]
    if WX[xw]['克'] == sw: return '贼'   # 下克上
    if WX[sw]['克'] == xw: return '克'   # 上克下
    return None

def is_yang_zhi(z):
    """判断地支阴阳：子寅辰午申戌=阳, 丑卯巳未酉亥=阴"""
    return DIZHI_NUM[z] % 2 == 0

def by_chuankou(chu, tianpan_zhi):
    """三传递进：中传=天盘[初传], 末传=天盘[中传]（上传法，已用大师奇门验证 2026-07-05）"""
    chu_idx = DIZHI_NUM[chu]
    zhong = tianpan_zhi[chu_idx]
    mo = tianpan_zhi[DIZHI_NUM[zhong]]
    return zhong, mo

def san_chuan(sike, ri_gan, tianpan_zhi):
    """九宗门法取三传"""
    ri_gan_wx = GAN_WUXING[ri_gan]
    
    # 收集贼克
    zeike_list = []
    for name, (shang, xia) in sike.items():
        r = check_ke_zei(shang, xia, ri_gan_wx)
        if r:
            zeike_list.append((name, shang, xia, r))
    
    if len(zeike_list) == 1:
        _, chu, _, r = zeike_list[0]
        ks = '元首' if r == '克' else '始入'
        return chu, *by_chuankou(chu, tianpan_zhi), ks
    
    if len(zeike_list) > 1:
        # 比用：取与日干同五行者
        for name, shang, xia, r in zeike_list:
            if WUXING_MAP[shang] == ri_gan_wx:
                return shang, *by_chuankou(shang, tianpan_zhi), '比用'
        # 涉害：取第一组
        for name, shang, xia, r in zeike_list:
            return shang, *by_chuankou(shang, tianpan_zhi), '涉害'

    # 伏吟无克不取遥克：阳日干上发用，阴日支上发用；再按刑递传。
    is_fuyin = all(tianpan_zhi[i] == DIZHI[i] for i in range(12))
    if is_fuyin:
        is_yang_day = TIANGAN_NUM[ri_gan] % 2 == 0
        chu = sike[1][0] if is_yang_day else sike[3][0]
        zhong = XING_NEXT[chu]
        if zhong == chu:
            raise NotImplementedError('伏吟自刑取传尚未实现，拒绝输出错误三传')
        mo = XING_NEXT[zhong]
        return chu, zhong, mo, '伏吟'
    
    # 遥克
    jigong = GAN_JIGONG[ri_gan]
    jigong_wx = WUXING_MAP[jigong]
    
    # 上神克日干 → 蒿矢
    haoshi = []
    for name, (shang, xia) in sike.items():
        sw = WUXING_MAP[shang]
        if WX[sw]['克'] == jigong_wx:
            haoshi.append((name, shang))
    
    if haoshi:
        if len(haoshi) == 1:
            chu = haoshi[0][1]
        else:
            # 比用：阳日取阳支，阴日取阴支
            ri_gan_yang = TIANGAN_NUM[ri_gan] % 2 == 0  # 甲丙戊庚壬=阳
            same_yin_yang = [(n,s) for n,s in haoshi if is_yang_zhi(s) == ri_gan_yang]
            chu = same_yin_yang[0][1] if same_yin_yang else haoshi[0][1]
        return chu, *by_chuankou(chu, tianpan_zhi), '蒿矢'
    
    # 日干克上神 → 弹射
    tanshe = []
    for name, (shang, xia) in sike.items():
        sw = WUXING_MAP[shang]
        if WX[jigong_wx]['克'] == sw:
            tanshe.append((name, shang))
    
    if tanshe:
        if len(tanshe) == 1:
            chu = tanshe[0][1]
        else:
            ri_gan_yang = TIANGAN_NUM[ri_gan] % 2 == 0
            same_yin_yang = [(n,s) for n,s in tanshe if is_yang_zhi(s) == ri_gan_yang]
            chu = same_yin_yang[0][1] if same_yin_yang else tanshe[0][1]
        return chu, *by_chuankou(chu, tianpan_zhi), '弹射'
    
    # 昴星
    chu_idx = (DIZHI_NUM['酉'] + 1) % 12
    chu = DIZHI[chu_idx]
    return chu, *by_chuankou(chu, tianpan_zhi), '昴星'

def guiren_bu(ri_gan, hour, shi_zhi):
    """排天将"""
    try:
        year = datetime.now().year
        dt = datetime(year, 7, 5, hour, 0)  # simplified
    except:
        dt = datetime(2026, 7, 5, hour, 0)
    
    # 日出约6点 日落约18点
    is_day = 6 <= hour < 18
    
    day_gui, night_gui = GUIREN_MAP.get(ri_gan, ('丑','未'))
    gui_dizhi = day_gui if is_day else night_gui
    gui_idx = DIZHI_NUM[gui_dizhi]
    
    # 贵人顺逆
    if 3 <= gui_idx <= 8:
        order = TIANJIANG_SHUN
    else:
        order = TIANJIANG_NI
    
    result = [None]*12
    for i in range(12):
        if 3 <= gui_idx <= 8:
            pos = (gui_idx + i) % 12  # 顺排：顺时针
        else:
            pos = (gui_idx - i) % 12  # 逆排：逆时针（已验证 2026-07-05 vs 大师奇门）
        result[pos] = order[i]
    return result

def get_liuqin(ri_gan_wx, dizhi):
    """地支五行对日干五行的六亲关系"""
    dw = WUXING_MAP[dizhi]
    if dw == ri_gan_wx: return '兄弟'
    if WX[ri_gan_wx]['克'] == dw: return '妻财'
    if WX[dw]['克'] == ri_gan_wx: return '官鬼'
    if WX[ri_gan_wx]['生'] == dw: return '子孙'
    if WX[dw]['生'] == ri_gan_wx: return '父母'
    return '?'

def dun_gan(ri_gan, shi_zhi):
    """遁干：五鼠遁基础"""
    start_map = {'甲':0,'乙':2,'丙':4,'丁':6,'戊':8,'己':0,'庚':2,'辛':4,'壬':6,'癸':8}
    start = start_map.get(ri_gan, 0)
    shi_idx = DIZHI_NUM[shi_zhi]
    dun_list = []
    for i in range(12):
        gan_idx = (start + ((i - shi_idx) % 12)) % 10
        dun_list.append(TIANGAN[gan_idx])
    return dun_list

# ==================== 主函数 ====================

def liuren(year, month, day, hour):
    """完整起盘"""
    ri_gan, ri_zhi = compute_ganzhi(year, month, day)
    shi_gan, shi_zhi = get_shichen_ganzhi(ri_gan, hour)
    yue_jiang = get_yue_jiang(month, day, year)
    tp = tianpan(yue_jiang, shi_zhi)
    sk = si_ke(ri_gan, ri_zhi, tp)
    chu, zhong, mo, keshi = san_chuan(sk, ri_gan, tp)
    tian_jiangs = guiren_bu(ri_gan, hour, shi_zhi)
    xun_kong = get_xun_kong(ri_gan, ri_zhi)
    dungan_list = dun_gan(ri_gan, shi_zhi)
    ri_gan_wx = GAN_WUXING[ri_gan]
    
    pan = []
    for i, d in enumerate(DIZHI):
        is_kong = d in xun_kong
        pan.append({
            '宫': d,
            '天盘': tp[i],
            '地盘': d,
            '天将': tian_jiangs[i],
            '六亲': get_liuqin(ri_gan_wx, tp[i]),
            '遁干': dungan_list[i] + tp[i],
            '旬空': is_kong
        })

    # 三传中的地支属于天盘，不能按同名地盘宫位直接取天将。
    # 在事实层预先完成反查，避免下游把“传支丑”误读成“地盘丑宫”。
    pan_by_tian = {item['天盘']: item for item in pan}
    chuan_details = {}
    for label, branch in (('初传', chu), ('中传', zhong), ('末传', mo)):
        item = pan_by_tian[branch]
        chuan_details[label] = {
            '传支': branch,
            '地盘': item['地盘'],
            '天将': item['天将'],
            '六亲': item['六亲'],
            '旬空': branch in xun_kong,
        }
    
    return {
        '时间': f'{year}-{month:02d}-{day:02d} {hour:02d}:00',
        '四柱': {
            '年': '丙午',
            '月': get_month_ganzhi(year, month, day),
            '日': f'{ri_gan}{ri_zhi}',
            '时': f'{shi_gan}{shi_zhi}'
        },
        '月将': yue_jiang,
        '占时': shi_zhi,
        '旬空': xun_kong,
        '天地盘': pan,
        '四课': {
            '第一课': f"{sk[1][0]}（上）\n{sk[1][1]}（下）",
            '第二课': f"{sk[2][0]}（上）\n{sk[2][1]}（下）",
            '第三课': f"{sk[3][0]}（上）\n{sk[3][1]}（下）",
            '第四课': f"{sk[4][0]}（上）\n{sk[4][1]}（下）",
        },
        '四课_raw': {str(k): {'上':v[0], '下':v[1]} for k,v in sk.items()},
        '三传': {'初传': chu, '中传': zhong, '末传': mo, '课式': keshi},
        '三传明细': chuan_details,
        '日干五行': ri_gan_wx
    }

def fmt_human(r):
    """人类可读输出"""
    lines = []
    lines.append(f"╔══════════════════════════╗")
    lines.append(f"║  大六壬课盘              ║")
    lines.append(f"╠══════════════════════════╣")
    lines.append(f"║ {r['时间']}                 ║")
    lines.append(f"║ 日柱: {r['四柱']['日']}  时柱: {r['四柱']['时']}    ║")
    lines.append(f"║ 月将: {r['月将']}  占时: {r['占时']}  旬空: {' '.join(r['旬空'])}  ║")
    lines.append(f"║ 课式: {r['三传']['课式']}                   ║")
    lines.append(f"╠══════════════════════════╣")
    lines.append(f"║ 三传: {r['三传']['初传']} → {r['三传']['中传']} → {r['三传']['末传']}            ║")
    if '三传明细' in r:
        for label in ('初传', '中传', '末传'):
            detail = r['三传明细'][label]
            kong = '（空）' if detail['旬空'] else ''
            lines.append(
                f"║ {label}: {detail['传支']}落{detail['地盘']} "
                f"乘{detail['天将']} {detail['六亲']}{kong} ║"
            )
    lines.append(f"╠══════════════════════════╣")
    lines.append(f"║ 天地盘                    ║")
    for g in r['天地盘']:
        kong = '◌' if g['旬空'] else ' '
        lines.append(f"║ {g['宫']} {g['遁干']}({g['天将']}){kong} →六亲:{g['六亲']}  ║")
    lines.append(f"╚══════════════════════════╝")
    return '\n'.join(lines)

if __name__ == '__main__':
    args = [a for a in sys.argv[1:] if not a.startswith('--')]
    use_json = '--json' in sys.argv
    
    if len(args) >= 4:
        y, m, d, h = int(args[0]), int(args[1]), int(args[2]), int(args[3])
    else:
        now = datetime.now()
        y, m, d, h = now.year, now.month, now.day, now.hour
    
    r = liuren(y, m, d, h)
    
    if use_json:
        print(json.dumps(r, ensure_ascii=False, indent=2))
    else:
        print(fmt_human(r))
        print()
        print(json.dumps(r, ensure_ascii=False, indent=2))
