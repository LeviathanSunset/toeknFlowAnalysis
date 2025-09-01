#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试新的API端点
"""

from solscanCrawler import SolscanAnalyzer
import json

def test_metadata_api():
    """测试代币metadata API"""
    print("🧪 测试新的代币metadata API...")
    
    token_address = "5zCETicUCJqJ5Z3wbfFPZqtSpHPYqnggs1wX7ZRpump"
    
    analyzer = SolscanAnalyzer()
    result = analyzer.get_token_metadata(token_address)
    
    if result:
        print("✅ API调用成功！")
        print("📋 获取到的字段:")
        for key, value in result.items():
            print(f"   {key}: {value}")
            
        if 'actual_total_supply' in result:
            print(f"\n🎉 成功获取总供应量: {result['actual_total_supply']:,.2f}")
        else:
            print("\n❌ 未获取到总供应量")
    else:
        print("❌ API调用失败")

if __name__ == "__main__":
    test_metadata_api()
