#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试优化后的地址分类
"""

import pandas as pd
import sys
import os

# 添加项目根目录到Python路径
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from analysis import TokenFlowAnalyzer

def test_optimized_classification():
    """测试优化后的地址分类"""
    print("🧪 测试优化后的地址分类")
    print("=" * 50)
    
    # 加载数据
    analyzer = TokenFlowAnalyzer()
    analyzer.load_data("storage/solscan_data_20250901_142013.json")
    analyzer.analyze_net_flows()
    
    df = analyzer.net_flows_df
    
    # 检查0流量分类问题
    zero_flow_marketmakers = df[
        (df['net_tokens'] == 0) & 
        (df['address_type'].str.contains('做市商|套利者', na=False))
    ]
    
    print(f"🚨 0流量被分类为做市商的地址: {len(zero_flow_marketmakers)} 个")
    
    # 统计各类型地址数量
    print("\n📊 优化后的地址类型统计:")
    type_counts = df['address_type'].value_counts()
    for addr_type, count in type_counts.items():
        print(f"   {addr_type}: {count} 个")
    
    # 测试真实交易地址过滤
    real_traders_df = df[df['address'].apply(analyzer._is_real_trader_address)]
    excluded_df = df[~df['address'].apply(analyzer._is_real_trader_address)]
    
    print(f"\n🏠 总地址数: {len(df)}")
    print(f"✅ 真实交易地址: {len(real_traders_df)}")
    print(f"❌ 排除的地址 (聚合器/池子/交易所): {len(excluded_df)}")
    
    print("\n🏷️ 被排除的地址:")
    for _, row in excluded_df.iterrows():
        address = row['address']
        label = analyzer.address_labels.get(address, "无标签")
        print(f"   📍 {address[:8]}...{address[-6:]} - {label}")
    
    # 计算优化后的平均值
    real_inflow_df = real_traders_df[real_traders_df['net_tokens'] > 0]
    real_outflow_df = real_traders_df[real_traders_df['net_tokens'] < 0]
    
    if len(real_inflow_df) > 0:
        avg_inflow = real_inflow_df['net_tokens'].sum() / len(real_inflow_df)
        print(f"\n📈 真实交易地址平均净流入: {avg_inflow:,.2f} 代币 (基于 {len(real_inflow_df)} 个地址)")
    
    if len(real_outflow_df) > 0:
        avg_outflow = abs(real_outflow_df['net_tokens'].sum()) / len(real_outflow_df)
        print(f"📉 真实交易地址平均净流出: {avg_outflow:,.2f} 代币 (基于 {len(real_outflow_df)} 个地址)")
    
    print("\n✅ 优化测试完成！")

if __name__ == "__main__":
    test_optimized_classification()
