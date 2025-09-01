#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
分析地址数量不匹配问题
"""

import pandas as pd
import sys
import os

# 添加项目根目录到Python路径
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from analysis import TokenFlowAnalyzer

def analyze_address_count_mismatch():
    """分析地址数量不匹配问题"""
    print("🔍 分析地址数量不匹配问题")
    print("=" * 50)
    
    # 加载数据
    analyzer = TokenFlowAnalyzer()
    analyzer.load_data("storage/solscan_data_20250901_142013.json")
    analyzer.analyze_net_flows()
    
    df = analyzer.net_flows_df
    
    # 统计所有地址
    total_addresses = len(df)
    net_inflow_addresses = len(df[df['net_tokens'] > 0])
    net_outflow_addresses = len(df[df['net_tokens'] < 0])
    zero_flow_addresses = len(df[df['net_tokens'] == 0])
    
    print(f"📊 总地址统计:")
    print(f"   🏠 总地址数: {total_addresses}")
    print(f"   📈 净流入地址: {net_inflow_addresses}")
    print(f"   📉 净流出地址: {net_outflow_addresses}")
    print(f"   ⚖️ 零流动地址: {zero_flow_addresses}")
    print(f"   🧮 净流入+净流出+零流动: {net_inflow_addresses + net_outflow_addresses + zero_flow_addresses}")
    
    # 过滤真实交易地址
    real_traders_df = df[df['address'].apply(analyzer._is_real_trader_address)]
    excluded_df = df[~df['address'].apply(analyzer._is_real_trader_address)]
    
    real_total = len(real_traders_df)
    real_inflow = len(real_traders_df[real_traders_df['net_tokens'] > 0])
    real_outflow = len(real_traders_df[real_traders_df['net_tokens'] < 0])
    real_zero = len(real_traders_df[real_traders_df['net_tokens'] == 0])
    
    print(f"\n📊 真实交易地址统计:")
    print(f"   ✅ 真实交易地址: {real_total}")
    print(f"   📈 真实净流入地址: {real_inflow}")
    print(f"   📉 真实净流出地址: {real_outflow}")
    print(f"   ⚖️ 真实零流动地址: {real_zero}")
    print(f"   🧮 真实净流入+净流出+零流动: {real_inflow + real_outflow + real_zero}")
    
    print(f"\n❌ 被排除地址: {len(excluded_df)}")
    
    # 分析零流动地址
    print(f"\n🔍 零流动地址详细分析:")
    zero_flow_df = df[df['net_tokens'] == 0]
    print(f"   总零流动地址: {len(zero_flow_df)}")
    
    for _, row in zero_flow_df.iterrows():
        address = row['address']
        label = analyzer.address_labels.get(address, "无标签")
        is_excluded = analyzer._is_excluded_address(address)
        status = "❌被排除" if is_excluded else "✅真实交易"
        print(f"   📍 {address[:8]}...{address[-6:]} - {label} - {status}")
        print(f"      净流动: {row['net_tokens']}, 流入: {row['inflow_tokens']:.2f}, 流出: {row['outflow_tokens']:.2f}")
    
    print(f"\n💡 结论:")
    print(f"   净流入地址({net_inflow_addresses}) + 净流出地址({net_outflow_addresses}) = {net_inflow_addresses + net_outflow_addresses}")
    print(f"   真实交易地址总数: {real_total}")
    print(f"   差异: {real_total - (net_inflow_addresses + net_outflow_addresses)} (这些是零流动地址)")

if __name__ == "__main__":
    analyze_address_count_mismatch()
