#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
代币流动净流入/流出分析工具
分析每个地址的净流入和净流出情况

作者: LeviathanSunset
版本: 1.0.0
"""

import json
import pandas as pd
import numpy as np
from pathlib import Path
import argparse
from datetime import datetime

class TokenFlowAnalyzer:
    """代币流动净流入/流出分析器"""
    
    def __init__(self, data_file=None):
        """
        初始化分析器
        
        Args:
            data_file: 数据文件路径（可选）
        """
        self.data_file = data_file
        self.df = None
        self.analysis_results = {}
        
    def load_data(self, file_path=None):
        """
        加载数据文件
        
        Args:
            file_path: 数据文件路径
        """
        if file_path:
            self.data_file = file_path
        
        if not self.data_file:
            # 查找最新的数据文件
            storage_dir = Path("storage")
            if storage_dir.exists():
                json_files = list(storage_dir.glob("solscan_data_*.json"))
                if json_files:
                    self.data_file = max(json_files, key=lambda x: x.stat().st_mtime)
                    print(f"🔍 自动选择最新数据文件: {self.data_file}")
                else:
                    raise FileNotFoundError("未找到数据文件")
            else:
                raise FileNotFoundError("storage 目录不存在")
        
        print(f"📂 加载数据文件: {self.data_file}")
        
        with open(self.data_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        if 'data' not in data:
            raise ValueError("数据文件格式错误，缺少 'data' 字段")
        
        self.df = pd.DataFrame(data['data'])
        print(f"✅ 成功加载 {len(self.df)} 条交易记录")
        
        # 数据预处理
        self._preprocess_data()
        
    def _preprocess_data(self):
        """数据预处理"""
        print("🔧 数据预处理中...")
        
        # 转换数据类型
        self.df['amount'] = pd.to_numeric(self.df['amount'], errors='coerce')
        self.df['value'] = pd.to_numeric(self.df['value'], errors='coerce')
        self.df['token_decimals'] = pd.to_numeric(self.df['token_decimals'], errors='coerce')
        self.df['block_time'] = pd.to_datetime(self.df['block_time'], unit='s', errors='coerce')
        
        # 计算实际代币数量（处理小数位）
        self.df['actual_amount'] = self.df['amount'] / (10 ** self.df['token_decimals'])
        
        # 获取代币地址（假设所有交易都是同一个代币）
        if 'token_address' in self.df.columns:
            token_address = self.df['token_address'].iloc[0]
            print(f"🔍 检测到代币地址: {token_address}")
            
            # 尝试从SolscanAnalyzer获取真实的总供应量
            try:
                from solscanCrawler import SolscanAnalyzer
                crawler = SolscanAnalyzer()
                metadata = crawler.get_token_metadata(token_address)
                
                if metadata and 'actual_total_supply' in metadata:
                    self.estimated_token_supply = metadata['actual_total_supply']
                    print(f"✅ 获取真实代币供应量: {self.estimated_token_supply:,.2f}")
                else:
                    # 如果获取失败，使用改进的估算方法
                    print("⚠️ 无法获取真实供应量，使用改进估算方法")
                    
                    total_volume = self.df['actual_amount'].sum()
                    max_single_amount = self.df['actual_amount'].max()
                    unique_addresses = len(set(self.df['from_address'].unique()) | set(self.df['to_address'].unique()))
                    
                    # 改进的估算逻辑：
                    # 1. 基于观察到的最大持仓估算
                    # 2. 考虑地址数量的影响
                    # 3. 为meme币和pump.fun代币调整参数
                    
                    if 'pump' in token_address.lower():
                        # pump.fun 代币通常供应量较大
                        estimated_multiplier = 50
                        print("🎯 检测到pump.fun代币，使用专用估算参数")
                    else:
                        estimated_multiplier = 20
                    
                    # 多种估算方法取最大值，确保不会低估
                    estimates = [
                        max_single_amount * estimated_multiplier,  # 基于最大单笔
                        total_volume * 10,  # 基于总交易量
                        max_single_amount * unique_addresses * 0.5  # 基于地址数量
                    ]
                    
                    self.estimated_token_supply = max(estimates)
                    print(f"📊 改进估算代币供应量: {self.estimated_token_supply:,.2f}")
                    print(f"   🔢 估算依据: 最大单笔 {max_single_amount:,.2f} × {estimated_multiplier}")
                    print(f"   👥 观察地址数: {unique_addresses}")
                    print(f"   📈 总交易量: {total_volume:,.2f}")
                    
            except ImportError:
                print("⚠️ 无法导入SolscanAnalyzer，使用估算方法")
                total_volume = self.df['actual_amount'].sum()
                max_single_amount = self.df['actual_amount'].max()
                self.estimated_token_supply = max(total_volume * 5, max_single_amount * 200)
                print(f"📊 估算代币供应量: {self.estimated_token_supply:,.2f}")
        else:
            # 如果没有token_address字段，使用估算方法
            total_volume = self.df['actual_amount'].sum()
            max_single_amount = self.df['actual_amount'].max()
            self.estimated_token_supply = max(total_volume * 5, max_single_amount * 200)
            print(f"📊 估算代币供应量: {self.estimated_token_supply:,.2f}")
        
        print(f"🔍 观察到的总交易量: {self.df['actual_amount'].sum():,.2f}")
        print(f"💰 最大单笔交易: {self.df['actual_amount'].max():,.2f}")
        
        # 处理缺失值
        self.df = self.df.dropna(subset=['from_address', 'to_address', 'amount', 'actual_amount'])
        
        print(f"💰 代币小数位: {self.df['token_decimals'].iloc[0]} 位")
        print(f"🔢 原始数量范围: {self.df['amount'].min():,.0f} - {self.df['amount'].max():,.0f}")
        print(f"🪙 实际代币数量范围: {self.df['actual_amount'].min():,.6f} - {self.df['actual_amount'].max():,.6f}")
        print(f"✅ 预处理完成，有效记录: {len(self.df)} 条")
    
    def calculate_net_flows(self):
        """
        计算每个地址的净流入/流出
        
        Returns:
            dict: 包含净流入/流出分析结果
        """
        print("📊 计算净流入/流出...")
        
        # 计算流出（作为发送方）- 基于代币数量
        outflows = self.df.groupby('from_address').agg({
            'actual_amount': 'sum',
            'amount': 'sum', 
            'value': 'sum',
            'trans_id': 'count'
        }).rename(columns={
            'actual_amount': 'outflow_tokens',
            'amount': 'outflow_raw_amount',
            'value': 'outflow_value',
            'trans_id': 'outflow_count'
        })
        
        # 计算流入（作为接收方）- 基于代币数量
        inflows = self.df.groupby('to_address').agg({
            'actual_amount': 'sum',
            'amount': 'sum',
            'value': 'sum',
            'trans_id': 'count'
        }).rename(columns={
            'actual_amount': 'inflow_tokens',
            'amount': 'inflow_raw_amount', 
            'value': 'inflow_value',
            'trans_id': 'inflow_count'
        })
        
        # 合并数据，创建完整的地址列表
        all_addresses = set(self.df['from_address'].unique()) | set(self.df['to_address'].unique())
        
        # 创建净流动分析表
        net_flows = []
        
        for address in all_addresses:
            # 获取流入数据
            inflow_tokens = inflows.loc[address, 'inflow_tokens'] if address in inflows.index else 0
            inflow_raw_amount = inflows.loc[address, 'inflow_raw_amount'] if address in inflows.index else 0
            inflow_value = inflows.loc[address, 'inflow_value'] if address in inflows.index else 0
            inflow_count = inflows.loc[address, 'inflow_count'] if address in inflows.index else 0
            
            # 获取流出数据
            outflow_tokens = outflows.loc[address, 'outflow_tokens'] if address in outflows.index else 0
            outflow_raw_amount = outflows.loc[address, 'outflow_raw_amount'] if address in outflows.index else 0
            outflow_value = outflows.loc[address, 'outflow_value'] if address in outflows.index else 0
            outflow_count = outflows.loc[address, 'outflow_count'] if address in outflows.index else 0
            
            # 计算净流动（基于代币数量）
            net_tokens = inflow_tokens - outflow_tokens
            net_value = inflow_value - outflow_value
            total_transactions = inflow_count + outflow_count
            
            # 计算比率（基于代币数量）
            if outflow_tokens > 0:
                flow_ratio = inflow_tokens / outflow_tokens
            elif inflow_tokens > 0:
                flow_ratio = float('inf')  # 只有流入，无流出
            else:
                flow_ratio = 0  # 无活动
            
            net_flows.append({
                'address': address,
                'inflow_tokens': inflow_tokens,
                'inflow_raw_amount': inflow_raw_amount,
                'inflow_value': inflow_value,
                'inflow_count': inflow_count,
                'outflow_tokens': outflow_tokens,
                'outflow_raw_amount': outflow_raw_amount,
                'outflow_value': outflow_value,
                'outflow_count': outflow_count,
                'net_tokens': net_tokens,
                'net_value': net_value,
                'total_transactions': total_transactions,
                'flow_ratio': flow_ratio,
                'address_type': self._classify_address_type(net_tokens, inflow_tokens, outflow_tokens, total_transactions)
            })
        
        self.net_flows_df = pd.DataFrame(net_flows)
        
        # 显示分类阈值信息
        whale_threshold = self.estimated_token_supply * 0.001
        large_holder_threshold = self.estimated_token_supply * 0.0005
        medium_threshold = self.estimated_token_supply * 0.0001
        
        print(f"✅ 完成 {len(self.net_flows_df)} 个地址的净流动计算")
        print("\n🏷️ 地址分类阈值 (基于流通量百分比):")
        print(f"   📊 估算代币供应量: {self.estimated_token_supply:,.2f}")
        print(f"   🐋 鲸鱼阈值 (0.1%): {whale_threshold:,.2f} 代币")
        print(f"   🏢 大户阈值 (0.05%): {large_holder_threshold:,.2f} 代币")  
        print(f"   📈 中等阈值 (0.01%): {medium_threshold:,.2f} 代币")
        
        return self.net_flows_df
    
    def _classify_address_type(self, net_tokens, inflow_tokens, outflow_tokens, total_transactions):
        """
        分类地址类型（基于代币流通量百分比）
        
        Args:
            net_tokens: 净代币流动
            inflow_tokens: 流入代币数量
            outflow_tokens: 流出代币数量
            total_transactions: 总交易数
        
        Returns:
            str: 地址类型
        """
        # 基于流通量百分比的阈值设置
        whale_threshold = self.estimated_token_supply * 0.001  # 0.1% 流通量
        large_holder_threshold = self.estimated_token_supply * 0.0005  # 0.05% 流通量
        medium_threshold = self.estimated_token_supply * 0.0001  # 0.01% 流通量
        
        active_threshold = 10    # 10笔交易
        
        # 计算地址的最大持仓影响（流入或流出的最大值）
        max_position = max(abs(inflow_tokens), abs(outflow_tokens))
        
        if total_transactions >= active_threshold:
            # 高频交易者
            if abs(net_tokens) < (whale_threshold * 0.1):  # 净流动很小（鲸鱼阈值的10%）
                if max_position >= whale_threshold:
                    return "大型做市商"
                else:
                    return "做市商/套利者"
            elif abs(net_tokens) >= whale_threshold:  # >= 0.1% 流通量
                if net_tokens > 0:
                    return "鲸鱼买入"
                else:
                    return "鲸鱼卖出"
            elif abs(net_tokens) >= large_holder_threshold:  # >= 0.05% 流通量
                if net_tokens > 0:
                    return "大买家"
                else:
                    return "大卖家"
            elif net_tokens > 0:
                return "活跃买家"
            else:
                return "活跃卖家"
        else:
            # 低频交易者
            if abs(net_tokens) >= whale_threshold:  # >= 0.1% 流通量
                if net_tokens > 0:
                    return "鲸鱼买入"
                else:
                    return "鲸鱼卖出"
            elif abs(net_tokens) >= large_holder_threshold:  # >= 0.05% 流通量
                if net_tokens > 0:
                    return "大户买入"
                else:
                    return "大户卖出"
            elif abs(net_tokens) >= medium_threshold:  # >= 0.01% 流通量
                if net_tokens > 0:
                    return "中等买家"
                else:
                    return "中等卖家"
            elif net_tokens > 0:
                return "普通买家"
            elif net_tokens < 0:
                return "普通卖家"
            else:
                return "无净流动"
    
    def get_top_net_inflows(self, top_n=20):
        """
        获取净流入最大的地址
        
        Args:
            top_n: 返回前N个地址
        
        Returns:
            pd.DataFrame: 净流入排行榜
        """
        if self.net_flows_df is None:
            self.calculate_net_flows()
        
        top_inflows = self.net_flows_df.nlargest(top_n, 'net_tokens')
        
        print("🏆 净流入最大的地址 (Top 20) - 按代币数量:")
        print("=" * 140)
        print(f"{'排名':<4} {'地址':<20} {'净流入(代币)':<15} {'流入(代币)':<15} {'流出(代币)':<15} {'交易数':<8} {'类型':<12}")
        print("=" * 140)
        
        for idx, row in top_inflows.iterrows():
            rank = top_inflows.index.get_loc(idx) + 1
            address = row['address'][:16] + "..." if len(row['address']) > 16 else row['address']
            print(f"{rank:<4} {address:<20} {row['net_tokens']:<15,.6f} {row['inflow_tokens']:<15,.6f} "
                  f"{row['outflow_tokens']:<15,.6f} {row['total_transactions']:<8} {row['address_type']:<12}")
        
        return top_inflows
    
    def get_top_net_outflows(self, top_n=20):
        """
        获取净流出最大的地址
        
        Args:
            top_n: 返回前N个地址
        
        Returns:
            pd.DataFrame: 净流出排行榜
        """
        if self.net_flows_df is None:
            self.calculate_net_flows()
        
        top_outflows = self.net_flows_df.nsmallest(top_n, 'net_tokens')
        
        print("\n📉 净流出最大的地址 (Top 20) - 按代币数量:")
        print("=" * 140)
        print(f"{'排名':<4} {'地址':<20} {'净流出(代币)':<15} {'流入(代币)':<15} {'流出(代币)':<15} {'交易数':<8} {'类型':<12}")
        print("=" * 140)
        
        for idx, row in top_outflows.iterrows():
            rank = top_outflows.index.get_loc(idx) + 1
            address = row['address'][:16] + "..." if len(row['address']) > 16 else row['address']
            net_outflow = abs(row['net_tokens'])
            print(f"{rank:<4} {address:<20} {net_outflow:<15,.6f} {row['inflow_tokens']:<15,.6f} "
                  f"{row['outflow_tokens']:<15,.6f} {row['total_transactions']:<8} {row['address_type']:<12}")
        
        return top_outflows
    
    def analyze_address_patterns(self):
        """分析地址行为模式"""
        if self.net_flows_df is None:
            self.calculate_net_flows()
        
        print("\n📈 地址行为模式分析:")
        print("=" * 80)
        
        # 按类型统计
        type_stats = self.net_flows_df['address_type'].value_counts()
        print("🏷️ 地址类型分布:")
        for addr_type, count in type_stats.items():
            percentage = count / len(self.net_flows_df) * 100
            print(f"   {addr_type}: {count} 个 ({percentage:.1f}%)")
        
        # 净流入/流出统计
        total_net_inflow = self.net_flows_df[self.net_flows_df['net_value'] > 0]['net_value'].sum()
        total_net_outflow = abs(self.net_flows_df[self.net_flows_df['net_value'] < 0]['net_value'].sum())
        
        print(f"\n💰 整体流动性分析:")
        print(f"   总净流入: ${total_net_inflow:,.2f}")
        print(f"   总净流出: ${total_net_outflow:,.2f}")
        print(f"   净差额: ${total_net_inflow - total_net_outflow:,.2f}")
        
        # 大户分析（净流动 > $1000）
        whales = self.net_flows_df[abs(self.net_flows_df['net_value']) > 1000]
        whale_buyers = whales[whales['net_value'] > 0]
        whale_sellers = whales[whales['net_value'] < 0]
        
        print(f"\n🐋 大户分析 (净流动 > $1,000):")
        print(f"   大买家数量: {len(whale_buyers)} 个")
        print(f"   大卖家数量: {len(whale_sellers)} 个")
        print(f"   大买家总流入: ${whale_buyers['net_value'].sum():,.2f}")
        print(f"   大卖家总流出: ${abs(whale_sellers['net_value'].sum()):,.2f}")
    
    def save_analysis_results(self, filename=None):
        """保存分析结果"""
        if filename is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"storage/net_flow_analysis_{timestamp}.json"
        
        results = {
            "analysis_time": datetime.now().isoformat(),
            "total_addresses": len(self.net_flows_df),
            "net_flows": self.net_flows_df.to_dict('records'),
            "summary": {
                "total_net_inflow": float(self.net_flows_df[self.net_flows_df['net_value'] > 0]['net_value'].sum()),
                "total_net_outflow": float(abs(self.net_flows_df[self.net_flows_df['net_value'] < 0]['net_value'].sum())),
                "address_type_distribution": self.net_flows_df['address_type'].value_counts().to_dict()
            }
        }
        
        # 确保目录存在
        Path(filename).parent.mkdir(parents=True, exist_ok=True)
        
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(results, f, ensure_ascii=False, indent=2, default=str)
        
        # 同时保存CSV格式
        csv_filename = filename.replace('.json', '.csv')
        self.net_flows_df.to_csv(csv_filename, index=False, encoding='utf-8-sig')
        
        print(f"\n💾 分析结果已保存:")
        print(f"   JSON: {filename}")
        print(f"   CSV:  {csv_filename}")
        
        return filename
    
    def run_full_analysis(self, data_file=None):
        """运行完整的净流入/流出分析"""
        print("🌟 代币流动净流入/流出分析开始")
        print("=" * 80)
        
        # 加载数据
        self.load_data(data_file)
        
        # 计算净流动
        self.calculate_net_flows()
        
        # 分析结果
        print("\n" + "=" * 80)
        top_inflows = self.get_top_net_inflows(20)
        top_outflows = self.get_top_net_outflows(20)
        
        # 分析模式
        self.analyze_address_patterns()
        
        # 保存结果
        saved_file = self.save_analysis_results()
        
        print("\n🎉 分析完成！")
        print(f"📊 分析了 {len(self.net_flows_df)} 个地址")
        print(f"📁 结果文件: {saved_file}")
        
        return {
            'net_flows': self.net_flows_df,
            'top_inflows': top_inflows,
            'top_outflows': top_outflows,
            'file': saved_file
        }

def main():
    """主函数"""
    parser = argparse.ArgumentParser(description='代币流动净流入/流出分析工具')
    parser.add_argument('--data', '-d', help='数据文件路径')
    parser.add_argument('--top', '-t', type=int, default=20, help='显示排行榜数量')
    
    args = parser.parse_args()
    
    try:
        analyzer = TokenFlowAnalyzer()
        result = analyzer.run_full_analysis(args.data)
        
        if result:
            print("\n✨ 所有分析完成！")
        
    except Exception as e:
        print(f"❌ 分析失败: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
