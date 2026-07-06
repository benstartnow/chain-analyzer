"""
chain-analyzer: 产业链全景图 HTML 渲染器
每个节点展示对应板块涨跌，一眼看清产业链冷暖
"""
import json
import os
from chain_data import build_report_json, get_stock_price


def node_html(items, layer_type="upstream"):
    """生成节点HTML，包含涨跌标签"""
    parts = []
    for n in items:
        chg = n.get("change")
        chg_tag = ""
        if chg is not None:
            cls = "up" if chg >= 0 else "down"
            sign = "+" if chg >= 0 else ""
            chg_tag = f'<span class="chg {cls}">{sign}{chg:.2f}%</span>'

        extra_cls = ""
        if layer_type == "midstream":
            extra_cls = " mid-node"

        parts.append(
            f'<div class="node{extra_cls}">'
            f'<span class="node-name">{n["name"]}</span>'
            f'<span class="node-desc">{n["desc"]}</span>'
            f'{chg_tag}'
            f'</div>'
        )
    return "".join(parts)


def render_chain_html(data):
    """生成产业链全景 HTML"""
    company = data["company"]
    chain = data["chain"]
    price = data.get("price")
    intro = data.get("introduction", "")
    mid_change = data.get("mid_change")
    sector_date = data.get("sector_date", "")

    name = company["name"]
    code = company["ts_code"]
    industry = company["industry"]

    upstream_nodes = node_html(chain.get("upstream", []), "upstream")
    midstream_nodes = node_html(chain.get("midstream", []), "midstream")
    downstream_nodes = node_html(chain.get("downstream", []), "downstream")

    # 公司自身涨跌 + 中游板块涨跌
    mid_tag = ""
    if mid_change is not None:
        cls = "up" if mid_change >= 0 else "down"
        sign = "+" if mid_change >= 0 else ""
        mid_tag = f'<span class="chg-badge {cls}">{chain.get("mid_index_name", "行业")} {sign}{mid_change:.2f}%</span>'

    stock_chg_tag = ""
    if price:
        pct = price.get("pct_chg", 0)
        if isinstance(pct, (int, float)):
            cls = "up" if pct >= 0 else "down"
            sign = "+" if pct >= 0 else ""
            stock_chg_tag = f'<span class="chg-badge {cls}">股价 {sign}{pct:.2f}%</span>'

    # 价格信息
    price_html = ""
    if price:
        chg_cls = "up" if price["pct_chg"] >= 0 else "down"
        chg_sign = "+" if price["pct_chg"] >= 0 else ""
        price_html = f"""
        <div class="price-bar">
            <div class="price-item">
                <span class="price-label">最新收盘</span>
                <span class="price-value">{price['close']}</span>
            </div>
            <div class="price-item">
                <span class="price-label">涨跌幅</span>
                <span class="price-value {chg_cls}">{chg_sign}{price['pct_chg']:.2f}%</span>
            </div>
            <div class="price-item">
                <span class="price-label">交易日期</span>
                <span class="price-value date">{price['trade_date']}</span>
            </div>
            <div class="price-item">
                <span class="price-label">最高</span>
                <span class="price-value">{price['high']}</span>
            </div>
            <div class="price-item">
                <span class="price-label">最低</span>
                <span class="price-value">{price['low']}</span>
            </div>
        </div>
        """

    intro_html = f'<p class="intro-text">{intro}</p>' if intro else ""
    sector_info = f'板块数据截止：{sector_date}' if sector_date else ""

    html = f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>{name} · 产业链全景</title>
<style>
* {{ margin: 0; padding: 0; box-sizing: border-box; }}
body {{
    background: #0b0d14;
    color: #e1e5eb;
    font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", "PingFang SC", "Hiragino Sans GB", "Microsoft YaHei", sans-serif;
    min-height: 100vh;
    display: flex;
    justify-content: center;
    padding: 24px;
}}
.container {{ max-width: 1000px; width: 100%; }}

.header {{
    text-align: center;
    padding: 32px 0 20px;
    border-bottom: 1px solid #1a1f2e;
    margin-bottom: 24px;
}}
.header h1 {{
    font-size: 22px;
    font-weight: 600;
    color: #f0f4ff;
}}
.header h1 .hl {{ color: #60a5fa; }}
.header .sub {{
    font-size: 13px;
    color: #6b7280;
    margin-top: 6px;
}}
.header .sub span {{ margin: 0 10px; }}

.price-bar {{
    display: flex;
    justify-content: center;
    gap: 16px;
    padding: 12px 0 20px;
    flex-wrap: wrap;
}}
.price-item {{
    text-align: center;
    background: #131724;
    border: 1px solid #1e2335;
    border-radius: 10px;
    padding: 10px 18px;
    min-width: 90px;
}}
.price-label {{
    font-size: 10px;
    color: #6b7280;
    letter-spacing: 0.5px;
    display: block;
    margin-bottom: 3px;
}}
.price-value {{
    font-size: 18px;
    font-weight: 600;
    color: #f0f4ff;
}}
.price-value.up {{ color: #ef4444; }}
.price-value.down {{ color: #22c55e; }}
.price-value.date {{ font-size: 13px; color: #9ca3af; font-weight: 400; }}

.chain-title {{
    display: flex;
    justify-content: center;
    align-items: center;
    gap: 12px;
    font-size: 13px;
    color: #6b7280;
    margin-bottom: 20px;
}}

.layer {{ margin-bottom: 10px; }}
.layer-header {{
    display: flex;
    align-items: center;
    justify-content: space-between;
    gap: 8px;
    font-size: 12px;
    font-weight: 600;
    color: #9ca3af;
    margin-bottom: 8px;
    padding-left: 4px;
}}
.layer-header .dot {{
    width: 8px; height: 8px; border-radius: 50%; display: inline-block;
}}
.dot-up {{ background: #f59e0b; }}
.dot-mid {{ background: #60a5fa; }}
.dot-down {{ background: #34d399; }}

.nodes {{
    display: flex;
    flex-wrap: wrap;
    gap: 8px;
    padding: 12px;
    background: #131724;
    border-radius: 12px;
    border: 1px solid #1e2335;
}}
.node {{
    background: #1b2236;
    border: 1px solid #252d44;
    border-radius: 8px;
    padding: 10px 14px;
    display: flex;
    flex-direction: column;
    align-items: center;
    min-width: 88px;
    flex: 1 0 auto;
    transition: all 0.15s;
    position: relative;
}}
.node:hover {{
    border-color: #3b82f6;
    background: #1e2940;
    transform: translateY(-1px);
}}
.node.mid-node {{
    border-color: #2563eb;
    background: linear-gradient(180deg, #1a2540, #1b2236);
}}
.node-name {{
    font-size: 13px;
    font-weight: 500;
    color: #e1e5eb;
}}
.node-desc {{
    font-size: 10px;
    color: #6b7280;
    font-weight: 400;
    margin-top: 2px;
}}
.chg {{
    font-size: 11px;
    font-weight: 600;
    margin-top: 4px;
    padding: 1px 8px;
    border-radius: 4px;
}}
.chg.up {{ color: #ef4444; background: rgba(239,68,68,0.12); }}
.chg.down {{ color: #22c55e; background: rgba(34,197,94,0.12); }}

.chg-badge {{
    font-size: 11px;
    font-weight: 600;
    padding: 2px 8px;
    border-radius: 4px;
    margin-left: 6px;
}}
.chg-badge.up {{ color: #ef4444; background: rgba(239,68,68,0.15); }}
.chg-badge.down {{ color: #22c55e; background: rgba(34,197,94,0.15); }}

.connector {{
    display: flex;
    justify-content: center;
    align-items: center;
    padding: 4px 0;
    color: #1e2335;
}}

.footer {{
    text-align: center;
    padding: 28px 0 16px;
    font-size: 11px;
    color: #374151;
    border-top: 1px solid #1a1f2e;
    margin-top: 24px;
}}

.legend {{
    display: flex;
    justify-content: center;
    gap: 24px;
    font-size: 11px;
    color: #6b7280;
    margin-top: 16px;
}}
.legend span {{ display: flex; align-items: center; gap: 4px; }}
.legend .box {{
    width: 12px; height: 12px; border-radius: 3px; display: inline-block;
}}

@media (max-width: 640px) {{
    .price-bar {{ gap: 10px; }}
    .price-item {{ min-width: 60px; padding: 6px 10px; }}
    .price-value {{ font-size: 15px; }}
    .node {{ min-width: 60px; padding: 8px 10px; }}
    body {{ padding: 12px; }}
}}
</style>
</head>
<body>
<div class="container">
    <div class="header">
        <h1>🏭 <span class="hl">{name}</span> · 产业链全景</h1>
        <div class="sub">
            {code} <span>|</span> {industry} <span>|</span> {company.get("area", "")}
            {stock_chg_tag}
        </div>
    </div>

    {price_html}
    {intro_html}

    <div class="chain-title">
        <span>⬆ 上游 · 原材料</span>
        <span style="color:#3b82f6;">●</span>
        <span>⬡ 中游 · 制造（公司位置）</span>
        <span style="color:#3b82f6;">●</span>
        <span>⬇ 下游 · 应用</span>
    </div>

    <div class="layer">
        <div class="layer-header">
            <span><span class="dot dot-up"></span> 上游 · 原材料 / 零部件 {mid_tag}</span>
        </div>
        <div class="nodes">{upstream_nodes}</div>
    </div>

    <div class="connector">▼</div>

    <div class="layer">
        <div class="layer-header">
            <span><span class="dot dot-mid"></span> 中游 · {chain.get("name", "")} {mid_tag}</span>
        </div>
        <div class="nodes">{midstream_nodes}</div>
    </div>

    <div class="connector">▼</div>

    <div class="layer">
        <div class="layer-header">
            <span><span class="dot dot-down"></span> 下游 · 应用 / 消费市场</span>
        </div>
        <div class="nodes">{downstream_nodes}</div>
    </div>

    <div class="legend">
        <span><span class="box" style="background:#ef4444;"></span> 上涨</span>
        <span><span class="box" style="background:#22c55e;"></span> 下跌</span>
        <span><span class="box" style="background:#6b7280;"></span> 板块涨跌幅</span>
    </div>

    <div class="footer">
        板块数据来源：同花顺行业/概念指数 · 股价来源：Tushare API · {sector_info} · 仅供参考，不构成投资建议
    </div>
</div>
</body>
</html>"""
    return html


def generate_report(ts_code, output_dir="."):
    """生成产业链全景HTML"""
    data = build_report_json(ts_code)
    if "error" in data and "chain" not in data:
        return {"error": data["error"]}

    html = render_chain_html(data)
    name = data["company"]["name"]
    os.makedirs(output_dir, exist_ok=True)
    filepath = os.path.join(output_dir, f"{name}_产业链全景_{ts_code[:6]}.html")
    with open(filepath, "w", encoding="utf-8") as f:
        f.write(html)
    return {"filepath": filepath, "size": len(html), "name": name, "code": ts_code}


if __name__ == "__main__":
    import sys
    code = sys.argv[1] if len(sys.argv) > 1 else "600580.SH"
    result = generate_report(code, ".")
    if "error" in result:
        print(f"❌ {result['error']}")
    else:
        print(f"✅ 报告已生成: {result['filepath']}")
        print(f"   名称: {result['name']} ({result['code']})")
        print(f"   大小: {result['size']:,} bytes")
