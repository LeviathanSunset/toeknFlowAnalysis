#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
调试数据加载问题的测试脚本
"""

import sys
import os
from pathlib import Path

# 添加项目根目录到Python路径
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from analysis import TokenFlowAnalyzer

def test_data_loading():
    """测试数据加载功能"""
    print("🧪 测试数据加载功能")
    print("=" * 50)
    
    # 检查storage目录
    storage_dir = Path("storage")
    if not storage_dir.exists():
        print("❌ storage 目录不存在")
        return
    
    # 查找JSON文件
    json_files = list(storage_dir.glob("*.json"))
    if not json_files:
        print("❌ 未找到JSON数据文件")
        return
    
    print(f"📁 找到 {len(json_files)} 个JSON文件:")
    for file in json_files:
        print(f"   - {file.name}")
    
    # 选择最新的文件
    latest_file = max(json_files, key=lambda x: x.stat().st_mtime)
    print(f"\n🎯 使用最新文件: {latest_file}")
    
    # 测试加载
    try:
        analyzer = TokenFlowAnalyzer()
        print("\n🔄 开始加载数据...")
        
        success = analyzer.load_data(str(latest_file))
        
        if success:
            print("✅ 数据加载成功！")
            print(f"📊 加载了 {len(analyzer.df)} 条记录")
            print(f"🏷️ 加载了 {len(analyzer.address_labels)} 个地址标签")
            
            # 显示数据框的基本信息
            print("\n📋 数据框信息:")
            print(f"   列数: {len(analyzer.df.columns)}")
            print(f"   列名: {list(analyzer.df.columns)}")
            print(f"   数据类型: {analyzer.df.dtypes.to_dict()}")
            
            # 测试分析
            print("\n🔍 测试净流动分析...")
            analyzer.analyze_net_flows()  # 使用别名方法
            print(f"✅ 分析完成！生成了 {len(analyzer.net_flows_df)} 个地址的净流动数据")
            
        else:
            print("❌ 数据加载失败")
            
    except Exception as e:
        print(f"💥 发生异常: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_data_loading()
