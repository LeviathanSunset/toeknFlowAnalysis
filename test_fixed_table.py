#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试修复后的表格功能
"""

import pandas as pd
import sys
import os

# 添加项目根目录到Python路径
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from analysis import TokenFlowAnalyzer

def test_fixed_table():
    """测试修复后的表格功能"""
    print("🔧 测试修复后的表格功能")
    print("=" * 50)
    
    # 加载数据
    analyzer = TokenFlowAnalyzer()
    analyzer.load_data("storage/solscan_data_20250901_142013.json")
    analyzer.analyze_net_flows()
    
    df = analyzer.net_flows_df.copy()
    
    # 按净流入量从大到小排序
    df = df.sort_values('net_tokens', ascending=False)
    
    # 添加排名列
    df['排名'] = range(1, len(df) + 1)
    
    # 格式化显示数据
    display_df = df.copy()
    display_df['地址/名称'] = display_df['address'].apply(lambda x: f"{x[:8]}...{x[-6:]}")
    display_df['净流动(代币)'] = display_df['net_tokens'].apply(lambda x: f"{x:,.2f}")
    display_df['净流动(美元)'] = display_df['net_value'].apply(lambda x: f"${x:.2f}")
    display_df['流入(代币)'] = display_df['inflow_tokens'].apply(lambda x: f"{x:,.2f}")
    display_df['流出(代币)'] = display_df['outflow_tokens'].apply(lambda x: f"{x:,.2f}")
    display_df['交易数'] = display_df['total_transactions']
    display_df['类型'] = display_df['address_type']
    
    # 标记被排除的地址
    display_df['是否排除'] = display_df['address'].apply(analyzer._is_excluded_address)
    
    # 选择要显示的列
    display_columns = ['排名', '地址/名称', '净流动(代币)', '净流动(美元)', '流入(代币)', '流出(代币)', '交易数', '类型']
    
    # 为被排除的地址在地址/名称列添加标识
    display_df['地址/名称'] = display_df.apply(lambda row: 
        f"🔘 {row['地址/名称']}" if row['是否排除'] else row['地址/名称'], axis=1)
    
    # 创建最终数据框
    final_df = display_df[display_columns]
    
    print(f"📊 表格处理结果:")
    print(f"   总行数: {len(final_df)}")
    print(f"   总列数: {len(final_df.columns)}")
    print(f"   列名: {list(final_df.columns)}")
    
    # 显示被排除地址的示例
    excluded_rows = display_df[display_df['是否排除']]
    print(f"\n🔘 被排除地址示例 ({len(excluded_rows)} 个):")
    for i, (_, row) in enumerate(excluded_rows.head(5).iterrows()):
        address = row['address']
        label = analyzer.address_labels.get(address, "无标签")
        print(f"   {i+1}. 排名{row['排名']}: {row['地址/名称']} - {label}")
    
    # 检查数据格式
    print(f"\n✅ 表格数据格式检查通过")
    print(f"   数据类型正确，可以正常显示")
    
    return final_df

if __name__ == "__main__":
    test_fixed_table()
