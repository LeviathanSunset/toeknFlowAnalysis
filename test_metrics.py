#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试修改后的指标计算
"""

import pandas as pd
import sys
import os

# 添加项目根目录到Python路径
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from analysis import TokenFlowAnalyzer

def test_metrics():
    """测试指标计算"""
    print("🧪 测试指标计算功能")
    print("=" * 50)
    
    # 加载数据
    analyzer = TokenFlowAnalyzer()
    analyzer.load_data("storage/solscan_data_20250901_142013.json")
    
    # 计算净流动
    analyzer.analyze_net_flows()
    
    # 获取净流动数据
    df = analyzer.net_flows_df
    
    # 计算关键指标
    total_addresses = len(df)
    net_inflow_addresses = len(df[df['net_tokens'] > 0])
    net_outflow_addresses = len(df[df['net_tokens'] < 0])
    
    # 计算净流入/净流入地址数比例和净流出/净流出地址数比例
    total_inflow_tokens = df[df['net_tokens'] > 0]['net_tokens'].sum()
    total_outflow_tokens = abs(df[df['net_tokens'] < 0]['net_tokens'].sum())
    
    # 计算平均每个净流入地址的流入量
    avg_inflow_per_address = total_inflow_tokens / net_inflow_addresses if net_inflow_addresses > 0 else 0
    # 计算平均每个净流出地址的流出量
    avg_outflow_per_address = total_outflow_tokens / net_outflow_addresses if net_outflow_addresses > 0 else 0
    
    print(f"📊 总地址数: {total_addresses:,}")
    print(f"📈 净流入地址: {net_inflow_addresses:,} ({net_inflow_addresses/total_addresses*100:.1f}%)")
    print(f"📉 净流出地址: {net_outflow_addresses:,} ({net_outflow_addresses/total_addresses*100:.1f}%)")
    print()
    print(f"💰 总净流入代币: {total_inflow_tokens:,.2f}")
    print(f"💰 总净流出代币: {total_outflow_tokens:,.2f}")
    print(f"📊 平均每个净流入地址: {avg_inflow_per_address:,.2f} 代币")
    print(f"📊 平均每个净流出地址: {avg_outflow_per_address:,.2f} 代币")
    print()
    print("✅ 指标计算完成！")

if __name__ == "__main__":
    test_metrics()
