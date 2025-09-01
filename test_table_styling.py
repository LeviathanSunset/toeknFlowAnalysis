#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试表格样式功能
"""

import pandas as pd
import sys
import os
import streamlit as st

# 添加项目根目录到Python路径
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from analysis import TokenFlowAnalyzer

def test_table_styling():
    """测试表格样式功能"""
    print("🎨 测试表格样式功能")
    print("=" * 50)
    
    # 加载数据
    analyzer = TokenFlowAnalyzer()
    analyzer.load_data("storage/solscan_data_20250901_142013.json")
    analyzer.analyze_net_flows()
    
    df = analyzer.net_flows_df.copy()
    
    # 按净流入量从大到小排序
    df = df.sort_values('net_tokens', ascending=False)
    
    # 格式化显示数据
    display_df = df.copy()
    display_df['排名'] = range(1, len(df) + 1)
    display_df['地址/名称'] = display_df['address'].apply(lambda x: f"{x[:8]}...{x[-6:]}")
    display_df['净流动(代币)'] = display_df['net_tokens'].apply(lambda x: f"{x:,.2f}")
    display_df['类型'] = display_df['address_type']
    
    # 标记被排除的地址
    display_df['是否排除'] = display_df['address'].apply(analyzer._is_excluded_address)
    
    print("📊 表格数据预览:")
    print(f"总地址数: {len(df)}")
    print(f"被排除地址数: {len(display_df[display_df['是否排除']])}")
    
    print("\n🔘 被排除的地址:")
    excluded_df = display_df[display_df['是否排除']]
    for _, row in excluded_df.iterrows():
        address = row['address']
        label = analyzer.address_labels.get(address, "无标签")
        print(f"   📍 排名{row['排名']}: {row['地址/名称']} - {label}")
    
    # 测试地址数量统计
    total_addresses = len(df)
    net_inflow_addresses = len(df[df['net_tokens'] > 0])
    net_outflow_addresses = len(df[df['net_tokens'] < 0])
    zero_flow_addresses = len(df[df['net_tokens'] == 0])
    
    print(f"\n📈 地址统计:")
    print(f"   总地址数: {total_addresses}")
    print(f"   净流入地址: {net_inflow_addresses}")
    print(f"   净流出地址: {net_outflow_addresses}")
    print(f"   零流动地址: {zero_flow_addresses}")
    print(f"   净流入+净流出: {net_inflow_addresses + net_outflow_addresses}")
    print(f"   是否匹配: {net_inflow_addresses + net_outflow_addresses + zero_flow_addresses == total_addresses}")
    
    print("\n✅ 表格样式测试完成！")

if __name__ == "__main__":
    test_table_styling()
