"""
chain-analyzer: 基本面选股 + 产业链全景报告
"""
import json, os, sys
sys.path.insert(0, os.path.dirname(__file__))
from chain_data import match_chain, get_sector_changes

import pandas as pd

def generate_value_report(output_dir="."):
    """生成基本面选股产业链分布报告"""
    df = pd.read_csv('/tmp/value_stocks.csv')
    
    # 产业链归类
    chain_map = {}
    for _, row in df.iterrows():
        ind = row['industry']
        chain = match_chain(ind)
        chain_name = chain['name'] if chain else "其他"
        if chain_name not in chain_map:
            chain_map[chain_name] = {
                'count': 0, 'industries': set(), 'stocks': [],
                'avg_pe': [], 'avg_pb': [], 'avg_dv': []
            }
        chain_map[chain_name]['count'] += 1
        chain_map[chain_name]['industries'].add(ind)
        chain_map[chain_name]['stocks'].append(row)
        if pd.notna(row['pe_ttm']) and row['pe_ttm'] > 0:
            chain_map[chain_name]['avg_pe'].append(row['pe_ttm'])
        if pd.notna(row['pb']) and row['pb'] > 0:
            chain_map[chain_name]['avg_pb'].append(row['pb'])
        if pd.notna(row['dv_ratio']):
            chain_map[chain_name]['avg_dv'].append(row['dv_ratio'])
    
    sorted_chains = sorted(chain_map.items(), key=lambda x: -x[1]['count'])
    
    # 获取板块涨跌
    all_sectors = []
    for name, info in sorted_chains:
        chain = None
        for ind in info['industries']:
            chain = match_chain(ind)
            if chain:
                break
        if chain and chain.get('mid_index'):
            all_sectors.append(chain['mid_index'])
    sector_data = get_sector_changes(all_sectors)
    
    # 构建 HTML
    chains_html = ""
    for name, info in sorted_chains:
        chain = None
        for ind in info['industries']:
            chain = match_chain(ind)
            if chain:
                break
        
        mid_chg = ""
        if chain and chain.get('mid_index') and chain['mid_index'] in sector_data:
            sd = sector_data[chain['mid_index']]
            cls = "up" if sd['pct'] >= 0 else "down"
            sign = "+" if sd['pct'] >= 0 else ""
            mid_chg = f'<span class="chg-badge {cls}">{sign}{sd["pct"]:.2f}%</span>'
        
        pct = info['count'] / len(df) * 100
        avg_pe = sum(info['avg_pe'])/len(info['avg_pe']) if info['avg_pe'] else 0
        avg_pb = sum(info['avg_pb'])/len(info['avg_pb']) if info['avg_pb'] else 0
        avg_dv = sum(info['avg_dv'])/len(info['avg_dv']) if info['avg_dv'] else 0
        
        top_stocks = sorted(info['stocks'], key=lambda x: -x['dv_ratio'])[:5]
        stocks_html = ""
        for s in top_stocks:
            stocks_html += f'<tr><td>{s["ts_code"][:6]}</td><td>{s["name"]}</td><td>{s["pe_ttm"]:.1f}</td><td>{s["pb"]:.2f}</td><td class="up">{s["dv_ratio"]:.1f}%</td></tr>'
        
        chains_html += f"""
        <div class="chain-card">
            <div class="chain-header">
                <span class="chain-name">{name}</span>
                <span class="chain-count">{info['count']} 只 ({pct:.1f}%)</span>
                {mid_chg}
            </div>
            <div class="chain-meta">
                <span>平均PE: {avg_pe:.1f}</span>
                <span>平均PB: {avg_pb:.2f}</span>
                <span>平均股息: {avg_dv:.1f}%</span>
            </div>
            <table class="stock-table">
                <tr><th>代码</th><th>名称</th><th>PE</th><th>PB</th><th>股息率</th></tr>
                {stocks_html}
            </table>
        </div>
        """
    
    html = f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>基本面选股 · 产业链分布</title>
<style>
* {{ margin: 0; padding: 0; box-sizing: border-box; }}
body {{ background: #0b0d14; color: #e1e5eb; font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", "PingFang SC", "Hiragino Sans GB", "Microsoft YaHei", sans-serif; padding: 24px; display: flex; justify-content: center; }}
.container {{ max-width: 960px; width: 100%; }}
.header {{ text-align: center; padding: 28px 0 20px; border-bottom: 1px solid #1a1f2e; margin-bottom: 24px; }}
.header h1 {{ font-size: 22px; font-weight: 600; color: #f0f4ff; }}
.header h1 .hl {{ color: #60a5fa; }}
.header .sub {{ font-size: 13px; color: #6b7280; margin-top: 6px; }}
.filter-bar {{ display: flex; justify-content: center; gap: 16px; flex-wrap: wrap; margin-bottom: 24px; }}
.filter-item {{ background: #131724; border: 1px solid #1e2335; border-radius: 10px; padding: 10px 16px; text-align: center; min-width: 80px; }}
.filter-label {{ font-size: 10px; color: #6b7280; display: block; }}
.filter-value {{ font-size: 16px; font-weight: 600; color: #f0f4ff; margin-top: 2px; }}
.chain-card {{ background: #131724; border: 1px solid #1e2335; border-radius: 12px; padding: 16px; margin-bottom: 12px; }}
.chain-header {{ display: flex; align-items: center; gap: 12px; margin-bottom: 8px; }}
.chain-name {{ font-size: 15px; font-weight: 600; color: #f0f4ff; }}
.chain-count {{ font-size: 12px; color: #6b7280; }}
.chain-meta {{ display: flex; gap: 16px; font-size: 11px; color: #9ca3af; margin-bottom: 10px; }}
.stock-table {{ width: 100%; border-collapse: collapse; font-size: 12px; }}
.stock-table th {{ text-align: left; color: #6b7280; padding: 6px 8px; border-bottom: 1px solid #1e2335; font-weight: 500; }}
.stock-table td {{ padding: 6px 8px; border-bottom: 1px solid #1a1f2e; color: #e1e5eb; }}
.stock-table tr:hover td {{ background: #1a1f2e; }}
.up {{ color: #ef4444; }}
.down {{ color: #22c55e; }}
.chg-badge {{ font-size: 11px; font-weight: 600; padding: 2px 8px; border-radius: 4px; }}
.chg-badge.up {{ color: #ef4444; background: rgba(239,68,68,0.15); }}
.chg-badge.down {{ color: #22c55e; background: rgba(34,197,94,0.15); }}
.footer {{ text-align: center; padding: 24px 0; font-size: 11px; color: #374151; }}
</style>
</head>
<body>
<div class="container">
    <div class="header">
        <h1>📊 基本面选股 · <span class="hl">产业链分布</span></h1>
        <div class="sub">筛选条件：PE<20 | PB<2 | 股息率>0.5% | 市值>50亿 | 排除ST/次新</div>
    </div>
    
    <div class="filter-bar">
        <div class="filter-item"><span class="filter-label">符合标的</span><span class="filter-value">{len(df)}</span></div>
        <div class="filter-item"><span class="filter-label">覆盖产业链</span><span class="filter-value">{len(sorted_chains)}</span></div>
        <div class="filter-item"><span class="filter-label">平均PE</span><span class="filter-value">{df['pe_ttm'].mean():.1f}</span></div>
        <div class="filter-item"><span class="filter-label">平均PB</span><span class="filter-value">{df['pb'].mean():.2f}</span></div>
        <div class="filter-item"><span class="filter-label">平均股息</span><span class="filter-value">{df['dv_ratio'].mean():.1f}%</span></div>
    </div>
    
    {chains_html}
    
    <div class="footer">数据来源：Tushare API · {df.iloc[0]['trade_date'] if 'trade_date' in df.columns else '20260703'} · 仅供参考，不构成投资建议</div>
</div>
</body>
</html>"""
    
    filepath = os.path.join(output_dir, "基本面选股_产业链分布.html")
    with open(filepath, "w", encoding="utf-8") as f:
        f.write(html)
    return {"filepath": filepath, "size": len(html), "count": len(df)}


if __name__ == "__main__":
    r = generate_value_report(".")
    print(f"✅ 报告已生成: {r['filepath']}")
    print(f"   标的数: {r['count']}")
    print(f"   大小: {r['size']:,} bytes")
