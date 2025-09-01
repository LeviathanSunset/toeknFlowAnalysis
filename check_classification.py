#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
检查地址分类问题
"""

import pandas as pd
import sys
import os

# 添加项目根目录到Python路径
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from analysis import TokenFlowAnalyzer

def check_classification_issues():
    """检查地址分类问题"""
    print("🔍 检查地址分类问题")
    print("=" * 50)
    
    # 加载数据
    analyzer = TokenFlowAnalyzer()
    analyzer.load_data("storage/solscan_data_20250901_142013.json")
    analyzer.analyze_net_flows()
    
    df = analyzer.net_flows_df
    
    # 查找0流量被分类为做市商的情况
    zero_flow_marketmakers = df[
        (df['net_tokens'] == 0) & 
        (df['address_type'].str.contains('做市商|套利者', na=False))
    ]
    
    print(f"🚨 发现 {len(zero_flow_marketmakers)} 个0流量被分类为做市商的地址:")
    for _, row in zero_flow_marketmakers.iterrows():
        address = row['address']
        label = analyzer.address_labels.get(address, "无标签")
        print(f"   📍 {address[:8]}...{address[-6:]} - {label} - {row['address_type']}")
        print(f"      净流动: {row['net_tokens']}, 流入: {row['inflow_tokens']}, 流出: {row['outflow_tokens']}, 交易数: {row['total_transactions']}")
    
    print()
    
    # 查找所有的聚合器、池子、交易所
    excluded_keywords = ['Exchange', 'Aggregator', 'AMM', 'Pool', 'Authority', 'CLMM', 'CPMM', 'DCA', 'Auction']
    excluded_addresses = []
    
    for address, label in analyzer.address_labels.items():
        if any(keyword in label for keyword in excluded_keywords):
            excluded_addresses.append(address)
    
    print(f"🏢 识别到 {len(excluded_addresses)} 个需要排除的地址 (聚合器/池子/交易所):")
    for address in excluded_addresses:
        label = analyzer.address_labels[address]
        if address in df['address'].values:
            row = df[df['address'] == address].iloc[0]
            print(f"   🏷️ {label}")
            print(f"      地址: {address[:8]}...{address[-6:]}")
            print(f"      净流动: {row['net_tokens']:.2f}, 交易数: {row['total_transactions']}")
    
    print()
    
    # 统计各类型地址数量
    print("📊 地址类型统计:")
    type_counts = df['address_type'].value_counts()
    for addr_type, count in type_counts.items():
        print(f"   {addr_type}: {count} 个")

if __name__ == "__main__":
    check_classification_issues()
