#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试cookies更新功能
直接访问 https://solscan.io/token/[代币地址] 来更新cookies
"""

import sys
import os

# 添加项目根目录到Python路径
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from solscanCrawler import SolscanAnalyzer

def test_cookie_update():
    """测试cookies更新功能"""
    # 使用配置文件中的代币地址进行测试
    test_token = "5zCETicUCJqJ5Z3wbfFPZqtSpHPYqnggs1wX7ZRpump"  # SPARK代币
    
    print("🧪 测试代币页面cookies更新功能")
    print(f"🎯 测试代币: {test_token}")
    print("=" * 60)
    
    try:
        # 初始化分析器
        analyzer = SolscanAnalyzer()
        
        print(f"📋 当前cf_clearance: {analyzer.config['cookies']['cf_clearance'][:50]}...")
        print()
        
        # 测试为特定代币更新cookies
        print("🔄 开始为代币页面更新cookies...")
        success = analyzer.update_cookies_for_token(test_token)
        
        if success:
            print()
            print("✅ 测试成功！")
            print(f"📋 新的cf_clearance: {analyzer.config['cookies']['cf_clearance'][:50]}...")
            
            # 测试获取代币信息以验证cookies是否有效
            print()
            print("🔍 测试获取代币信息...")
            metadata = analyzer.get_token_metadata(test_token)
            
            if metadata:
                print("✅ 代币信息获取成功，cookies有效！")
                if 'name' in metadata:
                    print(f"   代币名称: {metadata.get('name', 'N/A')}")
                if 'symbol' in metadata:
                    print(f"   代币符号: {metadata.get('symbol', 'N/A')}")
            else:
                print("⚠️ 无法获取代币信息，可能需要进一步调试")
        else:
            print("❌ 测试失败！")
            
    except Exception as e:
        print(f"❌ 测试过程中出现错误: {str(e)}")

if __name__ == "__main__":
    test_cookie_update()
