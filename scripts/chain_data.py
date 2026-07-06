"""
chain-analyzer: 产业链知识库 + 数据获取
根据股票代码获取公司行业分类，匹配产业链全景图谱并获取板块涨跌
"""
import json
import tushare as ts

# ===== 预设产业链知识图谱（含关联板块指数代码） =====
INDUSTRY_CHAINS = {
    "电气设备": {
        "name": "电气设备（电机/电控/变压器）",
        "mid_index": "861013.TI",
        "mid_index_name": "机械制造",
        "upstream": [
            {"name": "稀土永磁", "desc": "钕铁硼永磁材料", "sector": "885343.TI", "sector_name": "稀土永磁"},
            {"name": "硅钢片", "desc": "无取向/取向硅钢", "sector": "861126.TI", "sector_name": "钢铁"},
            {"name": "铜漆包线", "desc": "电磁线/漆包线", "sector": "861126.TI", "sector_name": "钢铁"},
            {"name": "精密轴承", "desc": "高速/高精度轴承", "sector": "861013.TI", "sector_name": "机械制造"},
            {"name": "铸件壳体", "desc": "铝/铸铁/钣金件", "sector": "861126.TI", "sector_name": "钢铁"},
            {"name": "绝缘材料", "desc": "绝缘漆/绝缘纸", "sector": "861112.TI", "sector_name": "商品化工"}
        ],
        "midstream": [
            {"name": "伺服电机", "desc": "精密运动控制", "sector": "861013.TI", "sector_name": "机械制造"},
            {"name": "工业电机", "desc": "高低压异步/同步电机", "sector": "861013.TI", "sector_name": "机械制造"},
            {"name": "防爆电机", "desc": "石化/煤矿特种电机", "sector": "861013.TI", "sector_name": "机械制造"},
            {"name": "微特电机", "desc": "日用/车载微型电机", "sector": "861013.TI", "sector_name": "机械制造"},
            {"name": "驱动电机", "desc": "新能源车牵引电机", "sector": "885431.TI", "sector_name": "新能源汽车"},
            {"name": "变压器", "desc": "电力/配电变压器", "sector": "861013.TI", "sector_name": "机械制造"}
        ],
        "downstream": [
            {"name": "新能源汽车", "desc": "乘用车/商用车电驱", "sector": "885431.TI", "sector_name": "新能源汽车"},
            {"name": "工业自动化", "desc": "智能制造/产线驱动", "sector": "861013.TI", "sector_name": "机械制造"},
            {"name": "人形机器人", "desc": "关节模组/伺服控制", "sector": "886069.TI", "sector_name": "人形机器人"},
            {"name": "暖通空调", "desc": "HVAC 风机/压缩机", "sector": "881131.TI", "sector_name": "白色家电"},
            {"name": "低空经济", "desc": "eVTOL/无人机电机", "sector": "886066.TI", "sector_name": "飞行汽车(eVTOL)"},
            {"name": "风电设备", "desc": "风力发电机", "sector": "861112.TI", "sector_name": "商品化工"}
        ]
    },
    "有色金属": {
        "name": "有色金属（采选/冶炼/加工）",
        "mid_index": "885343.TI",
        "mid_index_name": "稀土永磁",
        "upstream": [
            {"name": "矿产资源", "desc": "铜矿/铝土矿/铅锌矿", "sector": "861126.TI", "sector_name": "钢铁"},
            {"name": "稀有金属", "desc": "锂/钴/镍/稀土矿", "sector": "885343.TI", "sector_name": "稀土永磁"},
            {"name": "矿山机械", "desc": "采掘/破碎/选矿设备", "sector": "861013.TI", "sector_name": "机械制造"},
            {"name": "能源", "desc": "电力/煤炭/天然气", "sector": "861112.TI", "sector_name": "商品化工"}
        ],
        "midstream": [
            {"name": "冶炼", "desc": "电解铝/电解铜/粗炼", "sector": "861126.TI", "sector_name": "钢铁"},
            {"name": "加工", "desc": "板带/箔/管/棒/型材", "sector": "861126.TI", "sector_name": "钢铁"},
            {"name": "合金制造", "desc": "铝合金/铜合金/高温合金", "sector": "861126.TI", "sector_name": "钢铁"},
            {"name": "回收再生", "desc": "废金属回收再利用", "sector": "861126.TI", "sector_name": "钢铁"}
        ],
        "downstream": [
            {"name": "建筑地产", "desc": "铝门窗/铜管/钢结构", "sector": "861126.TI", "sector_name": "钢铁"},
            {"name": "汽车制造", "desc": "车身铝板/铜线束", "sector": "861023.TI", "sector_name": "汽车"},
            {"name": "电子电器", "desc": "PCB铜箔/散热器", "sector": "861112.TI", "sector_name": "商品化工"},
            {"name": "新能源", "desc": "锂电池/光伏/风电", "sector": "885431.TI", "sector_name": "新能源汽车"},
            {"name": "航空航天", "desc": "钛合金/高温合金", "sector": "885700.TI", "sector_name": "军工"}
        ]
    },
    "电子": {
        "name": "电子（半导体/元器件/消费电子）",
        "mid_index": "861112.TI",
        "mid_index_name": "商品化工",
        "upstream": [
            {"name": "硅片", "desc": "大硅片/抛光片/外延片", "sector": "861112.TI", "sector_name": "商品化工"},
            {"name": "光刻胶", "desc": "ArF/KrF 光刻胶", "sector": "861112.TI", "sector_name": "商品化工"},
            {"name": "电子气体", "desc": "高纯气体/特气", "sector": "861112.TI", "sector_name": "商品化工"},
            {"name": "靶材", "desc": "溅射靶材", "sector": "861112.TI", "sector_name": "商品化工"},
            {"name": "设备", "desc": "光刻机/刻蚀/薄膜设备", "sector": "861013.TI", "sector_name": "机械制造"}
        ],
        "midstream": [
            {"name": "芯片设计", "desc": "逻辑/模拟/存储", "sector": "885343.TI", "sector_name": "稀土永磁"},
            {"name": "晶圆制造", "desc": "Foundry 代工", "sector": "861112.TI", "sector_name": "商品化工"},
            {"name": "封装测试", "desc": "先进封装/测试", "sector": "861112.TI", "sector_name": "商品化工"},
            {"name": "PCB", "desc": "印制电路板", "sector": "861112.TI", "sector_name": "商品化工"},
            {"name": "被动元件", "desc": "电容/电阻/电感", "sector": "861112.TI", "sector_name": "商品化工"}
        ],
        "downstream": [
            {"name": "消费电子", "desc": "手机/PC/可穿戴", "sector": "861112.TI", "sector_name": "商品化工"},
            {"name": "汽车电子", "desc": "智驾/座舱芯片", "sector": "885545.TI", "sector_name": "汽车电子"},
            {"name": "AI服务器", "desc": "GPU/HBM/存储", "sector": "861112.TI", "sector_name": "商品化工"},
            {"name": "通信设备", "desc": "基站/光通信", "sector": "861023.TI", "sector_name": "汽车"},
            {"name": "工业控制", "desc": "MCU/传感器", "sector": "861013.TI", "sector_name": "机械制造"}
        ]
    },
    "汽车": {
        "name": "汽车（整车/零部件）",
        "mid_index": "861023.TI",
        "mid_index_name": "汽车",
        "upstream": [
            {"name": "钢材", "desc": "高强钢/热冲压钢", "sector": "861126.TI", "sector_name": "钢铁"},
            {"name": "铝合金", "desc": "车身铝板/铸造铝", "sector": "861126.TI", "sector_name": "钢铁"},
            {"name": "塑料橡胶", "desc": "内外饰/密封件/轮胎", "sector": "861112.TI", "sector_name": "商品化工"},
            {"name": "电子元件", "desc": "芯片/传感器/线束", "sector": "885545.TI", "sector_name": "汽车电子"},
            {"name": "电池", "desc": "动力电池/铅酸电池", "sector": "885431.TI", "sector_name": "新能源汽车"}
        ],
        "midstream": [
            {"name": "发动机/电驱", "desc": "燃油引擎/电驱系统", "sector": "861023.TI", "sector_name": "汽车"},
            {"name": "变速箱", "desc": "AT/DCT/CVT", "sector": "861023.TI", "sector_name": "汽车"},
            {"name": "底盘系统", "desc": "悬架/制动/转向", "sector": "861023.TI", "sector_name": "汽车"},
            {"name": "车身内外饰", "desc": "冲压/注塑/仪表板", "sector": "861023.TI", "sector_name": "汽车"},
            {"name": "整车制造", "desc": "冲焊涂总四大工艺", "sector": "861023.TI", "sector_name": "汽车"}
        ],
        "downstream": [
            {"name": "经销商", "desc": "4S店/维修保养", "sector": "861023.TI", "sector_name": "汽车"},
            {"name": "出行服务", "desc": "网约车/租车/货运", "sector": "861023.TI", "sector_name": "汽车"},
            {"name": "后市场", "desc": "配件/改装/二手车", "sector": "861023.TI", "sector_name": "汽车"},
            {"name": "报废回收", "desc": "拆解/材料回收", "sector": "861126.TI", "sector_name": "钢铁"}
        ]
    },
    "医药生物": {
        "name": "医药生物（药品/器械/服务）",
        "mid_index": "861112.TI",
        "mid_index_name": "商品化工",
        "upstream": [
            {"name": "原料药", "desc": "大宗/特色原料药", "sector": "861112.TI", "sector_name": "商品化工"},
            {"name": "药用辅料", "desc": "填充剂/粘合剂", "sector": "861112.TI", "sector_name": "商品化工"},
            {"name": "包装材料", "desc": "西林瓶/预灌封", "sector": "861112.TI", "sector_name": "商品化工"},
            {"name": "生命科学试剂", "desc": "抗体/酶/培养基", "sector": "861112.TI", "sector_name": "商品化工"}
        ],
        "midstream": [
            {"name": "化学制药", "desc": "仿制药/创新药", "sector": "861112.TI", "sector_name": "商品化工"},
            {"name": "生物制药", "desc": "抗体/疫苗/细胞治疗", "sector": "861112.TI", "sector_name": "商品化工"},
            {"name": "中药", "desc": "中药饮片/品牌OTC", "sector": "861112.TI", "sector_name": "商品化工"},
            {"name": "医疗器械", "desc": "设备/耗材/IVD", "sector": "861013.TI", "sector_name": "机械制造"},
            {"name": "CXO", "desc": "CRO/CDMO/CSO", "sector": "861112.TI", "sector_name": "商品化工"}
        ],
        "downstream": [
            {"name": "公立医院", "desc": "三甲/二级医院", "sector": "861112.TI", "sector_name": "商品化工"},
            {"name": "基层医疗", "desc": "社区卫生中心", "sector": "861112.TI", "sector_name": "商品化工"},
            {"name": "零售药店", "desc": "连锁/线上药房", "sector": "861112.TI", "sector_name": "商品化工"},
            {"name": "互联网医疗", "desc": "在线问诊/慢病管理", "sector": "861112.TI", "sector_name": "商品化工"}
        ]
    },
    "食品饮料": {
        "name": "食品饮料（加工/酿造/品牌）",
        "mid_index": "861112.TI",
        "mid_index_name": "商品化工",
        "upstream": [
            {"name": "农产品", "desc": "粮食/水果/蔬菜", "sector": "861112.TI", "sector_name": "商品化工"},
            {"name": "畜禽养殖", "desc": "猪/鸡/牛/奶", "sector": "861112.TI", "sector_name": "商品化工"},
            {"name": "水产品", "desc": "捕捞/养殖", "sector": "861112.TI", "sector_name": "商品化工"},
            {"name": "包装材料", "desc": "玻璃/塑料/铝罐", "sector": "861126.TI", "sector_name": "钢铁"}
        ],
        "midstream": [
            {"name": "食品加工", "desc": "肉制品/速冻/休闲", "sector": "861112.TI", "sector_name": "商品化工"},
            {"name": "白酒", "desc": "高端/次高端/光瓶", "sector": "861112.TI", "sector_name": "商品化工"},
            {"name": "啤酒", "desc": "工业/精酿", "sector": "861112.TI", "sector_name": "商品化工"},
            {"name": "乳制品", "desc": "常温/低温/奶粉", "sector": "861112.TI", "sector_name": "商品化工"},
            {"name": "调味品", "desc": "酱油/醋/复合调味", "sector": "861112.TI", "sector_name": "商品化工"},
            {"name": "饮料", "desc": "软饮/茶饮/功能饮料", "sector": "861112.TI", "sector_name": "商品化工"}
        ],
        "downstream": [
            {"name": "商超", "desc": "KA卖场/便利店", "sector": "861112.TI", "sector_name": "商品化工"},
            {"name": "电商", "desc": "综合/垂直/社区团购", "sector": "861112.TI", "sector_name": "商品化工"},
            {"name": "餐饮", "desc": "中餐/快餐/茶饮", "sector": "861112.TI", "sector_name": "商品化工"},
            {"name": "批发市场", "desc": "农贸/经销商", "sector": "861112.TI", "sector_name": "商品化工"}
        ]
    },
    "机械设备": {
        "name": "机械设备（专用/通用设备）",
        "mid_index": "861013.TI",
        "mid_index_name": "机械制造",
        "upstream": [
            {"name": "钢材", "desc": "结构钢/模具钢/不锈钢", "sector": "861126.TI", "sector_name": "钢铁"},
            {"name": "铸锻件", "desc": "精密铸造/锻造", "sector": "861126.TI", "sector_name": "钢铁"},
            {"name": "轴承", "desc": "滚动/滑动轴承", "sector": "861013.TI", "sector_name": "机械制造"},
            {"name": "液压件", "desc": "泵/阀/油缸", "sector": "861013.TI", "sector_name": "机械制造"},
            {"name": "电机", "desc": "伺服/步进电机", "sector": "861013.TI", "sector_name": "机械制造"},
            {"name": "数控系统", "desc": "CNC/PLC/驱动器", "sector": "861013.TI", "sector_name": "机械制造"}
        ],
        "midstream": [
            {"name": "工程机械", "desc": "挖掘机/起重机/装载机", "sector": "861013.TI", "sector_name": "机械制造"},
            {"name": "机床工具", "desc": "加工中心/刀具", "sector": "861013.TI", "sector_name": "机械制造"},
            {"name": "工业机器人", "desc": "工业/协作/特种机器人", "sector": "884218.TI", "sector_name": "机器人"},
            {"name": "纺织机械", "desc": "纺纱/织造/印染设备", "sector": "861013.TI", "sector_name": "机械制造"},
            {"name": "半导体设备", "desc": "刻蚀/薄膜/检测", "sector": "861013.TI", "sector_name": "机械制造"},
            {"name": "锂电设备", "desc": "涂布/卷绕/化成分容", "sector": "861013.TI", "sector_name": "机械制造"}
        ],
        "downstream": [
            {"name": "基建地产", "desc": "工程机械需求", "sector": "861126.TI", "sector_name": "钢铁"},
            {"name": "制造业", "desc": "自动化产线改造", "sector": "861013.TI", "sector_name": "机械制造"},
            {"name": "新能源", "desc": "锂电/光伏设备需求", "sector": "885431.TI", "sector_name": "新能源汽车"},
            {"name": "半导体", "desc": "芯片制造设备需求", "sector": "861112.TI", "sector_name": "商品化工"}
        ]
    }
}

# 行业别名映射
INDUSTRY_ALIAS = {
    "电气设备": "电气设备", "电力设备": "电气设备", "电机制造": "电气设备",
    "有色金属": "有色金属", "钢铁": "有色金属",
    "采掘": "有色金属", "煤炭": "有色金属",
    "石油石化": "有色金属", "化工": "机械设备", "基础化工": "机械设备",
    "建筑材料": "机械设备", "建筑装饰": "机械设备", "建筑": "机械设备",
    "机械设备": "机械设备", "机械": "机械设备",
    "国防军工": "机械设备", "军工": "机械设备",
    "汽车": "汽车",
    "家用电器": "汽车", "家电": "汽车",
    "食品饮料": "食品饮料", "食品": "食品饮料", "白酒": "食品饮料",
    "医药生物": "医药生物", "医药": "医药生物",
    "电子": "电子", "半导体": "电子",
    "计算机": "电子", "通信": "电子",
    "传媒": "电子",
    "房地产": "有色金属",
    "银行": "有色金属",
    "非银金融": "有色金属", "金融": "有色金属",
    "农林牧渔": "食品饮料", "农业": "食品饮料",
    "轻工制造": "机械设备", "纺织服装": "机械设备", "纺织": "机械设备",
    "商贸零售": "食品饮料", "商业": "食品饮料",
    "社会服务": "食品饮料",
    "公用事业": "有色金属", "电力": "有色金属",
    "环保": "机械设备",
    "交通运输": "有色金属",
    "综合": "机械设备"
}


def get_sector_changes(ts_code_list):
    """批量获取同花顺板块指数涨跌幅"""
    pro = ts.pro_api()
    result = {}
    for code in set(ts_code_list):
        if not code:
            continue
        try:
            df = pro.ths_daily(ts_code=code, start_date='20260601', end_date='20260706', limit=1)
            if not df.empty:
                row = df.iloc[0]
                result[code] = {
                    "pct": round(float(row["pct_change"]), 2),
                    "close": round(float(row["close"]), 2),
                    "date": row["trade_date"]
                }
            else:
                result[code] = {"pct": 0, "close": 0, "date": "-"}
        except:
            result[code] = {"pct": 0, "close": 0, "date": "-"}
    return result


def get_company_info(ts_code):
    """获取公司基本信息"""
    pro = ts.pro_api()
    try:
        df = pro.stock_basic(ts_code=ts_code)
        if df.empty:
            return None
        row = df.iloc[0]
        return {
            "ts_code": ts_code,
            "name": row.get("name", ""),
            "industry": row.get("industry", ""),
            "area": row.get("area", "")
        }
    except Exception as e:
        return {"error": str(e)}


def get_company_detail(ts_code):
    """获取公司详细介绍"""
    pro = ts.pro_api()
    try:
        df = pro.stock_company(ts_code=ts_code)
        if df.empty:
            return ""
        row = df.iloc[0]
        return row.get("introduction", "")
    except:
        return ""


def get_stock_price(ts_code):
    """获取最新股价"""
    pro = ts.pro_api()
    try:
        df = pro.daily(ts_code=ts_code, limit=2)
        if df.empty:
            return None
        latest = df.iloc[0]
        return {
            "close": latest.get("close", "-"),
            "pct_chg": round(float(latest.get("pct_chg", 0)), 2),
            "trade_date": latest.get("trade_date", "-"),
            "high": latest.get("high", "-"),
            "low": latest.get("low", "-"),
            "vol": latest.get("vol", "-"),
            "amount": latest.get("amount", "-")
        }
    except:
        return None


def match_chain(industry_name):
    """根据行业名称匹配产业链图谱"""
    if industry_name in INDUSTRY_CHAINS:
        return INDUSTRY_CHAINS[industry_name]
    if industry_name in INDUSTRY_ALIAS:
        return INDUSTRY_CHAINS.get(INDUSTRY_ALIAS[industry_name])
    return None


def build_report_json(ts_code):
    """构建完整产业链报告，含板块涨跌数据"""
    info = get_company_info(ts_code)
    if info is None or "error" in info:
        return {"error": f"无法获取{ts_code}的信息"}

    industry = info.get("industry", "")
    chain = match_chain(industry)
    if chain is None:
        return {"error": f"暂未收录「{industry}」行业的产业链图谱", "company": info}

    # 收集所有需要查询的板块代码
    all_codes = []
    for layer in ["upstream", "midstream", "downstream"]:
        for node in chain.get(layer, []):
            if node.get("sector"):
                all_codes.append(node["sector"])
    if chain.get("mid_index"):
        all_codes.append(chain["mid_index"])

    # 获取板块涨跌
    sector_data = get_sector_changes(all_codes)

    # 给每个节点注入涨跌数据
    chain_with_changes = dict(chain)
    for layer in ["upstream", "midstream", "downstream"]:
        enriched = []
        for node in chain.get(layer, []):
            n = dict(node)
            s_code = node.get("sector")
            if s_code and s_code in sector_data:
                n["change"] = sector_data[s_code]["pct"]
                n["sector_close"] = sector_data[s_code]["close"]
            else:
                n["change"] = None
            enriched.append(n)
        chain_with_changes[layer] = enriched

    # 中游板块涨跌
    mid_code = chain.get("mid_index")
    mid_change = sector_data.get(mid_code, {}).get("pct") if mid_code else None

    detail = get_company_detail(ts_code)
    price = get_stock_price(ts_code)

    return {
        "company": info,
        "introduction": detail[:300] if detail else "",
        "chain": chain_with_changes,
        "price": price,
        "mid_change": mid_change,
        "sector_date": sector_data.get(list(sector_data.keys())[0], {}).get("date", "-") if sector_data else "-"
    }


if __name__ == "__main__":
    result = build_report_json("600580.SH")
    print(json.dumps(result, ensure_ascii=False, indent=2)[:2000])
