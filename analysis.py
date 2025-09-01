#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
地址净流入净流出分析脚本
分析代币转账数据，计算所有地址的净流入和净流出排行榜
"""

import json
import argparse
import os
from collections import defaultdict
from datetime import datetime
from typing import Dict, List, Tuple


class TokenFlowAnalyzer:
    """代币流动分析器"""
    
    def __init__(self, json_file_path: str):
        """
        初始化分析器
        
        Args:
            json_file_path: JSON数据文件路径
        """
        self.json_file_path = json_file_path
        self.address_flows = defaultdict(lambda: {'inflow': 0, 'outflow': 0, 'net_flow': 0})
        self.total_transactions = 0
        self.total_volume = 0
        self.token_info = {}
        
    def load_data(self) -> bool:
        """
        加载JSON数据文件
        
        Returns:
            bool: 加载是否成功
        """
        try:
            print(f"📂 正在加载数据文件: {self.json_file_path}")
            
            if not os.path.exists(self.json_file_path):
                print(f"❌ 文件不存在: {self.json_file_path}")
                return False
                
            with open(self.json_file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                
            if not data.get('success', False):
                print("❌ 数据文件显示爬取失败")
                return False
                
            self.raw_data = data
            self.transactions = data.get('data', [])
            self.total_transactions = len(self.transactions)
            
            print(f"✅ 成功加载 {self.total_transactions} 条交易记录")
            print(f"📊 数据统计: 总页数 {data.get('total_pages', 0)}, 总记录数 {data.get('total_records', 0)}")
            
            if self.transactions:
                # 获取代币信息
                first_tx = self.transactions[0]
                self.token_info = {
                    'address': first_tx.get('token_address', ''),
                    'decimals': first_tx.get('token_decimals', 6)
                }
                print(f"🪙 代币地址: {self.token_info['address']}")
                print(f"🔢 代币精度: {self.token_info['decimals']}")
            
            return True
            
        except FileNotFoundError:
            print(f"❌ 文件未找到: {self.json_file_path}")
            return False
        except json.JSONDecodeError as e:
            print(f"❌ JSON解析错误: {e}")
            return False
        except Exception as e:
            print(f"❌ 加载数据时发生错误: {e}")
            return False
    
    def analyze_flows(self):
        """分析地址流入流出"""
        print("\n🔍 开始分析地址流动...")
        
        for tx in self.transactions:
            from_addr = tx.get('from_address', '')
            to_addr = tx.get('to_address', '')
            amount = float(tx.get('amount', 0))
            token_decimals = tx.get('token_decimals', 6)
            
            if not from_addr or not to_addr or amount <= 0:
                continue
            
            # 将原始数量转换为实际代币数量（考虑精度）
            token_amount = amount / (10 ** token_decimals)
                
            # 计算流出（from_address）
            self.address_flows[from_addr]['outflow'] += token_amount
            self.address_flows[from_addr]['net_flow'] -= token_amount
            
            # 计算流入（to_address）
            self.address_flows[to_addr]['inflow'] += token_amount
            self.address_flows[to_addr]['net_flow'] += token_amount
            
            self.total_volume += token_amount
        
        print(f"✅ 分析完成，共处理 {len(self.address_flows)} 个地址")
        print(f"🪙 总交易数量: {self.total_volume:,.2f} 代币")
    
    def get_top_addresses(self, sort_by: str = 'net_flow', limit: int = 50) -> List[Tuple[str, Dict]]:
        """
        获取排行榜
        
        Args:
            sort_by: 排序字段 ('net_flow', 'inflow', 'outflow')
            limit: 返回数量限制
            
        Returns:
            List[Tuple[str, Dict]]: 排序后的地址列表
        """
        if sort_by not in ['net_flow', 'inflow', 'outflow']:
            raise ValueError("sort_by 必须是 'net_flow', 'inflow', 或 'outflow'")
        
        # 按指定字段排序
        sorted_addresses = sorted(
            self.address_flows.items(),
            key=lambda x: x[1][sort_by],
            reverse=True
        )
        
        return sorted_addresses[:limit]
    
    def get_net_outflow_addresses(self, limit: int = 50) -> List[Tuple[str, Dict]]:
        """
        获取净流出排行榜（净流入为负值的地址，按绝对值从大到小排序）
        
        Args:
            limit: 返回数量限制
            
        Returns:
            List[Tuple[str, Dict]]: 净流出地址列表
        """
        # 只选择净流出的地址（net_flow < 0），按net_flow从小到大排序
        net_outflow_addresses = [
            (addr, flows) for addr, flows in self.address_flows.items()
            if flows['net_flow'] < 0
        ]
        
        # 按净流入值从小到大排序（负数越小表示净流出越多）
        sorted_addresses = sorted(
            net_outflow_addresses,
            key=lambda x: x[1]['net_flow'],
            reverse=False  # 从小到大
        )
        
        return sorted_addresses[:limit]
    
    def print_ranking(self, ranking_type: str = 'net_flow', limit: int = 20):
        """
        打印排行榜
        
        Args:
            ranking_type: 排行类型 ('net_flow', 'inflow', 'outflow')
            limit: 显示数量限制
        """
        title_map = {
            'net_flow': '📈 净流入排行榜（正值为净流入，负值为净流出）',
            'net_outflow': '📉 净流出排行榜（按流出金额排序）',
            'inflow': '💰 流入排行榜',
            'outflow': '💸 流出排行榜'
        }
        
        print(f"\n{title_map.get(ranking_type, '排行榜')}")
        print("=" * 80)
        print(f"{'排名':<5} {'地址':<45} {'代币数量':<20}")
        print("-" * 80)
        
        if ranking_type == 'net_outflow':
            top_addresses = self.get_net_outflow_addresses(limit)
        else:
            top_addresses = self.get_top_addresses(ranking_type, limit)
        
        for rank, (address, flows) in enumerate(top_addresses, 1):
            if ranking_type == 'net_outflow':
                amount = flows['net_flow']  # 这里是负值
                amount_str = f"-{abs(amount):,.2f}"
            else:
                amount = flows[ranking_type]
                
                # 格式化金额显示
                if ranking_type == 'net_flow':
                    if amount >= 0:
                        amount_str = f"+{amount:,.2f}"
                    else:
                        amount_str = f"-{abs(amount):,.2f}"
                else:
                    amount_str = f"{amount:,.2f}"
            
            print(f"{rank:<5} {address:<45} {amount_str:<20}")
    
    def save_analysis_report(self, output_file: str = None):
        """
        保存分析报告到文件
        
        Args:
            output_file: 输出文件路径，如果为None则自动生成
        """
        if output_file is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_file = f"storage/analysis_report_{timestamp}.json"
            
        # 确保输出目录存在
        os.makedirs(os.path.dirname(output_file), exist_ok=True)
        
        # 准备报告数据
        report = {
            "analysis_info": {
                "input_file": self.json_file_path,
                "analysis_time": datetime.now().isoformat(),
                "total_addresses": len(self.address_flows),
                "total_transactions": self.total_transactions,
                "total_volume": self.total_volume,
                "token_info": self.token_info
            },
            "rankings": {
                "net_flow_top50": [
                    {
                        "rank": i + 1,
                        "address": addr,
                        "net_flow": flows['net_flow'],
                        "inflow": flows['inflow'],
                        "outflow": flows['outflow']
                    }
                    for i, (addr, flows) in enumerate(self.get_top_addresses('net_flow', 50))
                ],
                "net_outflow_top50": [
                    {
                        "rank": i + 1,
                        "address": addr,
                        "net_flow": flows['net_flow'],
                        "inflow": flows['inflow'],
                        "outflow": flows['outflow']
                    }
                    for i, (addr, flows) in enumerate(self.get_net_outflow_addresses(50))
                ],
                "inflow_top50": [
                    {
                        "rank": i + 1,
                        "address": addr,
                        "inflow": flows['inflow'],
                        "net_flow": flows['net_flow'],
                        "outflow": flows['outflow']
                    }
                    for i, (addr, flows) in enumerate(self.get_top_addresses('inflow', 50))
                ],
                "outflow_top50": [
                    {
                        "rank": i + 1,
                        "address": addr,
                        "outflow": flows['outflow'],
                        "net_flow": flows['net_flow'],
                        "inflow": flows['inflow']
                    }
                    for i, (addr, flows) in enumerate(self.get_top_addresses('outflow', 50))
                ]
            },
            "all_addresses": {
                addr: flows for addr, flows in self.address_flows.items()
            }
        }
        
        try:
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(report, f, indent=2, ensure_ascii=False)
            
            print(f"\n💾 分析报告已保存到: {output_file}")
            return output_file
            
        except Exception as e:
            print(f"❌ 保存报告时发生错误: {e}")
            return None
    
    def print_summary(self):
        """打印分析摘要"""
        print("\n" + "="*60)
        print("📊 分析摘要")
        print("="*60)
        print(f"📁 数据文件: {self.json_file_path}")
        print(f"🏷️  代币地址: {self.token_info.get('address', 'N/A')}")
        print(f"📈 总交易记录: {self.total_transactions:,}")
        print(f"🏠 涉及地址数: {len(self.address_flows):,}")
        print(f"🪙 总交易数量: {self.total_volume:,.2f} 代币")
        
        # 计算一些统计数据
        net_inflows = [f['net_flow'] for f in self.address_flows.values() if f['net_flow'] > 0]
        net_outflows = [f['net_flow'] for f in self.address_flows.values() if f['net_flow'] < 0]
        
        print(f"📈 净流入地址数: {len(net_inflows):,}")
        print(f"📉 净流出地址数: {len(net_outflows):,}")
        
        if net_inflows:
            print(f"💎 最大净流入: {max(net_inflows):,.2f} 代币")
        if net_outflows:
            print(f"💸 最大净流出: {abs(min(net_outflows)):,.2f} 代币")


def main():
    """主函数"""
    parser = argparse.ArgumentParser(description='分析代币转账数据，计算地址净流入净流出排行榜')
    parser.add_argument('json_file', help='输入的JSON数据文件路径')
    parser.add_argument('-o', '--output', help='输出报告文件路径（可选）')
    parser.add_argument('-l', '--limit', type=int, default=20, help='显示排行榜数量限制（默认20）')
    parser.add_argument('--no-save', action='store_true', help='不保存分析报告')
    
    args = parser.parse_args()
    
    # 创建分析器
    analyzer = TokenFlowAnalyzer(args.json_file)
    
    # 加载数据
    if not analyzer.load_data():
        return
    
    # 执行分析
    analyzer.analyze_flows()
    
    # 显示摘要
    analyzer.print_summary()
    
    # 显示排行榜
    analyzer.print_ranking('net_flow', args.limit)
    analyzer.print_ranking('net_outflow', args.limit)
    analyzer.print_ranking('inflow', args.limit)
    analyzer.print_ranking('outflow', args.limit)
    
    # 保存报告
    if not args.no_save:
        output_file = analyzer.save_analysis_report(args.output)
        if output_file:
            print(f"\n🎉 分析完成！报告已保存到: {output_file}")


if __name__ == "__main__":
    # 如果没有命令行参数，使用默认的数据文件
    import sys
    if len(sys.argv) == 1:
        # 查找最新的数据文件
        storage_dir = "storage"
        if os.path.exists(storage_dir):
            json_files = [f for f in os.listdir(storage_dir) if f.startswith('solscan_data_') and f.endswith('.json')]
            if json_files:
                # 按文件名排序，取最新的
                latest_file = sorted(json_files)[-1]
                json_file_path = os.path.join(storage_dir, latest_file)
                
                print(f"🔍 未指定输入文件，使用最新的数据文件: {json_file_path}")
                
                analyzer = TokenFlowAnalyzer(json_file_path)
                if analyzer.load_data():
                    analyzer.analyze_flows()
                    analyzer.print_summary()
                    analyzer.print_ranking('net_flow', 20)
                    analyzer.print_ranking('net_outflow', 20)
                    analyzer.print_ranking('inflow', 20)
                    analyzer.print_ranking('outflow', 20)
                    analyzer.save_analysis_report()
                    print("\n🎉 分析完成！")
            else:
                print("❌ storage目录中未找到数据文件")
        else:
            print("❌ storage目录不存在")
    else:
        main()
