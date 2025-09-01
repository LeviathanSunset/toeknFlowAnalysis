#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Solscan代币流动分析 - Streamlit可视化应用
展示各个地址的净流入和净流出分析

作者: LeviathanSunset
版本: 1.0.0
"""

import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import json
from pathlib import Path
from datetime import datetime
import time
import sys
import os

# 添加项目根目录到Python路径
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# 导入自定义分析模块
try:
    from analysis import TokenFlowAnalyzer
    from solscanCrawler import SolscanAnalyzer
except ImportError as e:
    st.error(f"无法导入分析模块: {str(e)}")
    st.error("请确保 analysis.py 和 solscanCrawler.py 文件存在")
    st.stop()

# 页面配置
st.set_page_config(
    page_title="Solscan代币流动分析",
    page_icon="🔍",
    layout="wide",
    initial_sidebar_state="expanded"
)

# 自定义CSS样式
st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        font-weight: bold;
        color: #1f77b4;
        text-align: center;
        margin-bottom: 2rem;
        padding: 1rem;
        background: linear-gradient(90deg, #f0f8ff, #e6f3ff);
        border-radius: 10px;
        border: 2px solid #1f77b4;
    }
    
    .metric-container {
        background-color: #f8f9fa;
        padding: 1rem;
        border-radius: 10px;
        border-left: 4px solid #1f77b4;
        margin: 1rem 0;
    }
    
    .net-inflow {
        color: #28a745;
        font-weight: bold;
    }
    
    .net-outflow {
        color: #dc3545;
        font-weight: bold;
    }
    
    .stDataFrame {
        border: 1px solid #dee2e6;
        border-radius: 5px;
    }
    
    .address-cell {
        font-family: 'Courier New', monospace;
        font-size: 0.9rem;
    }
</style>
""", unsafe_allow_html=True)

class StreamlitTokenFlowApp:
    """Streamlit代币流动分析应用"""
    
    def __init__(self):
        self.analyzer = None
        self.data_loaded = False
        self.net_flows_df = None
        
    def initialize_session_state(self):
        """初始化会话状态"""
        if 'analyzer' not in st.session_state:
            st.session_state.analyzer = None
        if 'data_loaded' not in st.session_state:
            st.session_state.data_loaded = False
        if 'crawl_in_progress' not in st.session_state:
            st.session_state.crawl_in_progress = False
        if 'crawl_config' not in st.session_state:
            st.session_state.crawl_config = {
                'token_address': '5zCETicUCJqJ5Z3wbfFPZqtSpHPYqnggs1wX7ZRpump',
                'max_pages': 50,
                'value_filter': 0.0
            }
    
    def load_available_data_files(self):
        """加载可用的数据文件"""
        storage_dir = Path("storage")
        if not storage_dir.exists():
            return []
        
        # 查找JSON数据文件
        json_files = list(storage_dir.glob("*.json"))
        json_files.sort(key=lambda x: x.stat().st_mtime, reverse=True)  # 按修改时间排序
        
        return [str(f) for f in json_files]
    
    def format_address(self, address, max_length=20, analyzer=None):
        """格式化地址显示"""
        if not address:
            return "N/A"
        
        # 尝试获取地址标签
        if analyzer and hasattr(analyzer, 'address_labels') and address in analyzer.address_labels:
            label = analyzer.address_labels[address]
            return f"🏷️ {label[:max_length]}..." if len(label) > max_length else f"🏷️ {label}"
        
        # 显示地址的前后部分
        if len(address) > max_length:
            return f"{address[:8]}...{address[-6:]}"
        else:
            return address
    
    def format_currency(self, value):
        """格式化货币显示"""
        if pd.isna(value):
            return "$0.00"
        
        if abs(value) >= 1e6:
            return f"${value/1e6:.2f}M"
        elif abs(value) >= 1e3:
            return f"${value/1e3:.2f}K"
        else:
            return f"${value:.2f}"
    
    def format_tokens(self, value):
        """格式化代币数量显示"""
        if pd.isna(value):
            return "0"
        
        if abs(value) >= 1e6:
            return f"{value/1e6:.2f}M"
        elif abs(value) >= 1e3:
            return f"{value/1e3:.2f}K"
        elif abs(value) >= 1:
            return f"{value:,.2f}"
        else:
            return f"{value:.6f}"
    
    def get_address_type_color(self, address_type):
        """根据地址类型返回颜色"""
        color_map = {
            "鲸鱼买入": "#004d25",      # 深绿色
            "鲸鱼卖出": "#8b0000",      # 深红色
            "大型做市商": "#ff6b35",     # 橙红色
            "大户买入": "#28a745",      # 绿色
            "大户卖出": "#dc3545",      # 红色
            "大买家": "#28a745",        # 绿色
            "大卖家": "#dc3545",        # 红色
            "中等买家": "#6f42c1",      # 紫色
            "中等卖家": "#e83e8c",      # 粉红色
            "活跃买家": "#17a2b8",      # 青色
            "活跃卖家": "#fd7e14",      # 橙色
            "普通买家": "#20c997",      # 薄荷绿
            "普通卖家": "#ffc107",      # 黄色
            "做市商/套利者": "#6c757d",  # 灰色
            "无净流动": "#adb5bd"       # 浅灰色
        }
        return color_map.get(address_type, "#6c757d")
    
    def render_header(self):
        """渲染页面头部"""
        st.markdown("""
        <div class="main-header">
            🔍 Solscan代币流动分析平台
        </div>
        """, unsafe_allow_html=True)
        
        st.markdown("""
        <div style="text-align: center; margin-bottom: 2rem; color: #666;">
            实时分析代币交易流动，识别净流入和净流出最大的地址
        </div>
        """, unsafe_allow_html=True)
    
    def render_sidebar(self):
        """渲染侧边栏"""
        st.sidebar.title("📊 分析控制面板")
        
        # 选择操作模式
        st.sidebar.subheader("🚀 操作模式")
        operation_mode = st.sidebar.radio(
            "选择操作:",
            ["📂 使用现有数据", "🔄 爬取新数据"],
            help="选择使用现有数据文件还是爬取新数据"
        )
        
        selected_file = None
        crawl_config = None
        
        if operation_mode == "📂 使用现有数据":
            # 数据文件选择
            st.sidebar.subheader("📂 数据源选择")
            data_files = self.load_available_data_files()
            
            if not data_files:
                st.sidebar.warning("未找到数据文件！请选择 '🔄 爬取新数据' 模式。")
                return None
            
            # 显示文件信息
            file_options = []
            for file_path in data_files:
                file_name = Path(file_path).name
                file_time = datetime.fromtimestamp(Path(file_path).stat().st_mtime)
                file_size = Path(file_path).stat().st_size / 1024  # KB
                display_name = f"{file_name} ({file_time.strftime('%m-%d %H:%M')}, {file_size:.1f}KB)"
                file_options.append((display_name, file_path))
            
            selected_option = st.sidebar.selectbox(
                "选择数据文件:",
                options=range(len(file_options)),
                format_func=lambda x: file_options[x][0],
                help="选择要分析的数据文件，默认为最新文件"
            )
            
            selected_file = file_options[selected_option][1] if file_options else None
            
        else:
            # 爬取配置
            st.sidebar.subheader("🕸️ 爬取配置")
            
            token_address = st.sidebar.text_input(
                "代币地址:",
                value=st.session_state.crawl_config['token_address'],
                help="要爬取的代币合约地址"
            )
            
            col1, col2 = st.sidebar.columns(2)
            with col1:
                max_pages = st.sidebar.number_input(
                    "最大页数:",
                    min_value=1,
                    max_value=200,
                    value=st.session_state.crawl_config['max_pages'],
                    help="限制爬取的最大页数"
                )
            
            with col2:
                value_filter = st.sidebar.number_input(
                    "价值过滤($):",
                    min_value=0.0,
                    max_value=1000.0,
                    value=float(st.session_state.crawl_config['value_filter']),
                    help="只爬取价值大于此值的交易"
                )
            
            # 时间范围配置
            st.sidebar.subheader("⏰ 时间范围 (可选)")
            use_time_filter = st.sidebar.checkbox("启用时间过滤", value=False)
            
            from_time = None
            to_time = None
            
            if use_time_filter:
                # 简化的时间输入
                st.sidebar.markdown("**开始时间**")
                from_datetime_str = st.sidebar.text_input(
                    "开始时间 (格式: YYYY-MM-DD HH:MM:SS)",
                    value="2025-08-30 09:00:00",
                    help="例如: 2025-08-30 09:00:00"
                )
                
                st.sidebar.markdown("**结束时间**")
                to_datetime_str = st.sidebar.text_input(
                    "结束时间 (格式: YYYY-MM-DD HH:MM:SS)",
                    value="2025-08-30 10:00:00",
                    help="例如: 2025-08-30 10:00:00"
                )
                
                # 解析时间字符串
                try:
                    from_datetime = datetime.strptime(from_datetime_str, "%Y-%m-%d %H:%M:%S")
                    to_datetime = datetime.strptime(to_datetime_str, "%Y-%m-%d %H:%M:%S")
                    
                    from_time = int(from_datetime.timestamp())
                    to_time = int(to_datetime.timestamp())
                    
                    # 验证时间范围
                    if to_time <= from_time:
                        st.sidebar.error("⚠️ 结束时间必须大于开始时间")
                        from_time = None
                        to_time = None
                    else:
                        # 显示选择的时间范围和时长
                        duration_hours = (to_time - from_time) / 3600
                        st.sidebar.success(f"✅ 时间范围: {duration_hours:.1f} 小时")
                        st.sidebar.info(f"📅 {from_datetime.strftime('%m-%d %H:%M')} 至 {to_datetime.strftime('%m-%d %H:%M')}")
                        
                except ValueError:
                    st.sidebar.error("❌ 时间格式错误，请使用 YYYY-MM-DD HH:MM:SS 格式")
                    from_time = None
                    to_time = None
            
            crawl_config = {
                'token_address': token_address,
                'max_pages': max_pages,
                'value_filter': value_filter,
                'from_time': from_time,
                'to_time': to_time
            }
            
            # 更新session state
            st.session_state.crawl_config = crawl_config
        
        # Cookies管理
        st.sidebar.subheader("🔧 Cookies管理")
        
        if operation_mode == "🔄 爬取新数据" and token_address:
            if st.sidebar.button(
                "🍪 更新Cookies",
                help=f"为代币 {token_address} 更新cookies，直接访问其代币页面"
            ):
                try:
                    with st.spinner("正在更新cookies..."):
                        # 初始化爬虫
                        crawler = SolscanAnalyzer()
                        success = crawler.update_cookies_for_token(token_address)
                        
                        if success:
                            st.sidebar.success("✅ Cookies更新成功！")
                        else:
                            st.sidebar.error("❌ Cookies更新失败")
                except Exception as e:
                    st.sidebar.error(f"❌ 更新失败: {str(e)}")
        else:
            st.sidebar.info("💡 请先输入代币地址以启用cookies更新功能")
        
        # 执行按钮
        st.sidebar.subheader("🎯 执行操作")
        
        if operation_mode == "📂 使用现有数据":
            analyze_button = st.sidebar.button(
                "🚀 开始分析",
                type="primary",
                width='stretch',
                help="分析选定的数据文件"
            )
            crawl_button = False
        else:
            crawl_button = st.sidebar.button(
                "🕸️ 爬取并分析",
                type="primary",
                width='stretch',
                help="爬取新数据并立即开始分析",
                disabled=st.session_state.crawl_in_progress
            )
            analyze_button = False
            
            if st.session_state.crawl_in_progress:
                st.sidebar.info("🔄 正在爬取数据，请稍候...")
        
        return {
            'operation_mode': operation_mode,
            'selected_file': selected_file,
            'crawl_config': crawl_config,
            'analyze_button': analyze_button,
            'crawl_button': crawl_button
        }
    
    def render_flow_charts(self, analyzer, top_n=20):
        """渲染流动图表"""
        st.subheader("📈 净流动可视化")
        
        df = analyzer.net_flows_df
        
        # 创建双列布局
        col1, col2 = st.columns(2)
        
        with col1:
            # 净流入排行榜 (代币数量)
            st.markdown("#### 🏆 净流入排行榜 (代币)")
            top_inflows = df.nlargest(top_n, 'net_tokens')
            
            if not top_inflows.empty:
                fig_inflow = px.bar(
                    top_inflows.head(10),
                    x='net_tokens',
                    y=top_inflows.head(10)['address'].apply(lambda x: self.format_address(x, 12, analyzer)),
                    orientation='h',
                    color='address_type',
                    color_discrete_map={t: self.get_address_type_color(t) for t in top_inflows['address_type'].unique()},
                    title=f"前10名净流入地址（代币数量）",
                    labels={'net_tokens': '净流入 (代币)', 'y': '地址'}
                )
                fig_inflow.update_layout(height=400, yaxis={'categoryorder': 'total ascending'})
                st.plotly_chart(fig_inflow, width='stretch')
        
        with col2:
            # 净流出排行榜 (代币数量)
            st.markdown("#### 📉 净流出排行榜 (代币)")
            top_outflows = df.nsmallest(top_n, 'net_tokens')
            
            if not top_outflows.empty:
                # 转换为正值用于显示
                top_outflows_display = top_outflows.head(10).copy()
                top_outflows_display['net_outflow'] = abs(top_outflows_display['net_tokens'])
                
                fig_outflow = px.bar(
                    top_outflows_display,
                    x='net_outflow',
                    y=top_outflows_display['address'].apply(lambda x: self.format_address(x, 12, analyzer)),
                    orientation='h',
                    color='address_type',
                    color_discrete_map={t: self.get_address_type_color(t) for t in top_outflows_display['address_type'].unique()},
                    title=f"前10名净流出地址（代币数量）",
                    labels={'net_outflow': '净流出 (代币)', 'y': '地址'}
                )
                fig_outflow.update_layout(height=400, yaxis={'categoryorder': 'total ascending'})
                st.plotly_chart(fig_outflow, width='stretch')
    
    def render_all_addresses_table(self, analyzer):
        """渲染所有地址的详细表格，按净流入量排序"""
        st.subheader("📋 完整地址表 - 按净流量排序")
        
        df = analyzer.net_flows_df.copy()
        
        # 按净流入量从大到小排序（从大流入到大流出）
        df = df.sort_values('net_tokens', ascending=False)
        
        # 添加排名列
        df['排名'] = range(1, len(df) + 1)
        
        # 格式化显示数据
        display_df = df.copy()
        display_df['地址/名称'] = display_df['address'].apply(lambda x: self.format_address(x, 25, analyzer))
        display_df['净流动(代币)'] = display_df['net_tokens'].apply(self.format_tokens)
        display_df['净流动(美元)'] = display_df['net_value'].apply(self.format_currency)
        display_df['流入(代币)'] = display_df['inflow_tokens'].apply(self.format_tokens)
        display_df['流出(代币)'] = display_df['outflow_tokens'].apply(self.format_tokens)
        display_df['交易数'] = display_df['total_transactions']
        display_df['类型'] = display_df['address_type']
        
        # 标记被排除的地址
        display_df['是否排除'] = display_df['address'].apply(analyzer._is_excluded_address)
        
        # 选择要显示的列
        display_columns = ['排名', '地址/名称', '净流动(代币)', '净流动(美元)', '流入(代币)', '流出(代币)', '交易数', '类型']
        
        # 为被排除的地址在地址/名称列添加标识
        display_df['地址/名称'] = display_df.apply(lambda row: 
            f"🔘 {row['地址/名称']}" if row['是否排除'] else row['地址/名称'], axis=1)
        
        # 直接显示数据框，不使用复杂的样式
        final_df = display_df[display_columns]
        
        # 显示完整数据表
        st.dataframe(
            final_df,
            width='stretch',
            height=800,
            use_container_width=True
        )
        
        # 添加说明
        st.markdown("""
        **🔍 表格说明：**
        - 🟢 **正常显示**：真实交易地址
        - 🔘 **带圆圈标识**：被排除的地址（聚合器、池子、交易所等）
        - 排序方式：按净流量从大流入到大流出排序
        """)
        
        # 移除了底部统计信息，统计数据已移至顶部
        
        # 下载按钮
        csv = final_df.to_csv(index=False, encoding='utf-8-sig')
        st.download_button(
            label="📥 下载完整数据为CSV",
            data=csv,
            file_name=f"complete_addresses_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
            mime="text/csv"
        )
    
    def load_and_analyze_data(self, file_path, min_value_threshold=0):
        """加载和分析数据"""
        try:
            # 显示进度
            progress_bar = st.progress(0)
            status_text = st.empty()
            
            # 初始化分析器
            status_text.text("🔄 初始化分析器...")
            progress_bar.progress(10)
            
            analyzer = TokenFlowAnalyzer()
            
            # 加载数据
            status_text.text("📂 加载数据文件...")
            progress_bar.progress(30)
            
            success = analyzer.load_data(file_path)
            if not success:
                progress_bar.empty()
                status_text.empty()
                st.error("❌ 数据加载失败")
                st.error("请检查数据文件格式是否正确")
                return None
            
            # 分析净流动
            status_text.text("🔍 分析净流动...")
            progress_bar.progress(60)
            
            analyzer.calculate_net_flows()
            
            # 应用筛选
            if min_value_threshold > 0:
                status_text.text("🎯 应用价值筛选...")
                progress_bar.progress(80)
                
                analyzer.filter_by_value(min_value_threshold)
            
            # 完成
            status_text.text("✅ 分析完成！")
            progress_bar.progress(100)
            
            time.sleep(0.5)  # 让用户看到完成状态
            progress_bar.empty()
            status_text.empty()
            
            return analyzer
            
        except Exception as e:
            progress_bar.empty()
            status_text.empty()
            st.error(f"❌ 分析过程中出现错误: {str(e)}")
            st.error("请检查数据文件格式或联系技术支持")
            return None
    
    def crawl_and_analyze_data(self, config):
        """爬取并分析数据"""
        try:
            st.session_state.crawl_in_progress = True
            
            # 显示进度
            progress_bar = st.progress(0)
            status_text = st.empty()
            
            # 初始化爬虫
            status_text.text("🔄 初始化爬虫...")
            progress_bar.progress(5)
            
            crawler = SolscanAnalyzer()
            
            # 开始爬取
            status_text.text("🕸️ 开始爬取数据...")
            progress_bar.progress(10)
            
            all_data = []
            page = 1
            max_pages = config['max_pages']
            
            while page <= max_pages:
                status_text.text(f"📡 爬取第 {page}/{max_pages} 页...")
                progress = 10 + int((page / max_pages) * 60)
                progress_bar.progress(progress)
                
                data = crawler.get_token_transfers(
                    address=config['token_address'],
                    page=page,
                    from_time=config.get('from_time'),
                    to_time=config.get('to_time'),
                    value_filter=config.get('value_filter')
                )
                
                if not data or not data.get('data'):
                    status_text.text(f"⚠️ 第 {page} 页无数据，停止爬取")
                    break
                
                all_data.extend(data['data'])
                page += 1
                
                time.sleep(0.5)  # 防止请求过快
            
            if not all_data:
                st.error("❌ 未爬取到任何数据")
                return None
            
            # 保存数据
            status_text.text("💾 保存爬取数据...")
            progress_bar.progress(75)
            
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            file_path = f"storage/solscan_data_{timestamp}.json"
            
            os.makedirs("storage", exist_ok=True)
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(all_data, f, ensure_ascii=False, indent=2)
            
            # 分析数据
            status_text.text("🔍 分析爬取数据...")
            progress_bar.progress(85)
            
            analyzer = TokenFlowAnalyzer()
            success = analyzer.load_data(file_path)
            
            if not success:
                st.error("❌ 数据分析失败")
                return None
            
            analyzer.calculate_net_flows()
            
            # 完成
            status_text.text("✅ 爬取和分析完成！")
            progress_bar.progress(100)
            
            time.sleep(0.5)
            progress_bar.empty()
            status_text.empty()
            
            st.success(f"🎉 成功爬取 {len(all_data)} 条交易记录！")
            
            return analyzer
            
        except Exception as e:
            st.error(f"❌ 爬取过程中出现错误: {str(e)}")
            return None
        finally:
            st.session_state.crawl_in_progress = False
    
    def render_summary_metrics(self, analyzer):
        """渲染总结指标"""
        st.subheader("📊 总体概览")
        
        df = analyzer.net_flows_df
        
        # 计算关键指标
        total_addresses = len(df)
        net_inflow_addresses = len(df[df['net_tokens'] > 0])
        net_outflow_addresses = len(df[df['net_tokens'] < 0])
        total_net_tokens = df['net_tokens'].sum()
        total_net_value = df['net_value'].sum()
        
        # 过滤出真实交易地址（排除聚合器、池子、交易所）
        real_traders_df = df[df['address'].apply(analyzer._is_real_trader_address)]
        
        # 计算真实交易地址的统计数据
        real_inflow_df = real_traders_df[real_traders_df['net_tokens'] > 0]
        real_outflow_df = real_traders_df[real_traders_df['net_tokens'] < 0]
        
        real_total_inflow_tokens = real_inflow_df['net_tokens'].sum() if len(real_inflow_df) > 0 else 0
        real_total_outflow_tokens = abs(real_outflow_df['net_tokens'].sum()) if len(real_outflow_df) > 0 else 0
        
        # 计算平均每个真实净流入地址的流入量
        avg_inflow_per_address = real_total_inflow_tokens / len(real_inflow_df) if len(real_inflow_df) > 0 else 0
        # 计算平均每个真实净流出地址的流出量
        avg_outflow_per_address = real_total_outflow_tokens / len(real_outflow_df) if len(real_outflow_df) > 0 else 0
        
        # 获取最大净流入和净流出
        max_inflow = df['net_tokens'].max()
        max_outflow = df['net_tokens'].min()
        
        # 显示指标
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.metric(
                label="🏠 总地址数",
                value=f"{total_addresses:,}",
                delta=f"真实交易: {len(real_traders_df):,}",
                help=f"参与交易的唯一地址总数 (包含 {total_addresses - len(real_traders_df)} 个聚合器/池子/交易所)"
            )
        
        with col2:
            st.metric(
                label="📈 净流入地址",
                value=f"{net_inflow_addresses:,}",
                delta=f"平均: {self.format_tokens(avg_inflow_per_address)}",
                help=f"净流入为正的地址数量 (占比: {net_inflow_addresses/total_addresses*100:.1f}%) \n平均值基于 {len(real_inflow_df)} 个真实交易地址计算"
            )
        
        with col3:
            st.metric(
                label="� 净流出地址",
                value=f"{net_outflow_addresses:,}",
                delta=f"平均: {self.format_tokens(avg_outflow_per_address)}",
                delta_color="inverse",
                help=f"净流出为负的地址数量 (占比: {net_outflow_addresses/total_addresses*100:.1f}%)"
            )
    
    def run(self):
        """运行应用程序"""
        self.initialize_session_state()
        
        # 渲染页面
        self.render_header()
        
        # 侧边栏
        sidebar_config = self.render_sidebar()
        
        if not sidebar_config:
            st.warning("请配置爬取参数或选择现有数据文件。")
            st.stop()
        
        # 处理用户操作
        if sidebar_config['analyze_button']:
            # 分析现有数据
            if sidebar_config['selected_file']:
                analyzer = self.load_and_analyze_data(sidebar_config['selected_file'])
                if analyzer:
                    st.session_state.analyzer = analyzer
                    st.session_state.data_loaded = True
                    st.rerun()
        
        elif sidebar_config['crawl_button']:
            # 爬取新数据
            if sidebar_config['crawl_config']:
                analyzer = self.crawl_and_analyze_data(sidebar_config['crawl_config'])
                if analyzer:
                    st.session_state.analyzer = analyzer
                    st.session_state.data_loaded = True
                    st.rerun()
        
        # 显示分析结果
        if st.session_state.data_loaded and st.session_state.analyzer:
            analyzer = st.session_state.analyzer
            
            # 显示总结指标
            self.render_summary_metrics(analyzer)
            
            # 显示图表
            self.render_flow_charts(analyzer, 20)  # 使用默认的显示数量
            
            # 显示完整地址表
            self.render_all_addresses_table(analyzer)
            
        else:
            # 欢迎页面
            st.markdown("""
            ## 🔍 代币流动分析工具
            
            ### 功能特点：
            - 🕸️ **实时数据爬取**: 从Solscan API获取最新交易数据
            - 📊 **净流动分析**: 自动计算每个地址的净流入/净流出
            - 🏷️ **地址标签识别**: 自动识别地址类型（鲸鱼、做市商等）
            - 📈 **可视化图表**: 直观展示流动趋势和排行榜
            - 📋 **完整数据表**: 详细的地址流动信息
            - 💾 **数据导出**: 支持CSV格式下载
            
            ### 使用方法：
            1. 在左侧选择操作模式（使用现有数据或爬取新数据）
            2. 配置相应的参数
            3. 点击执行按钮开始分析
            4. 查看分析结果和可视化图表
            
            ### 开始使用：
            👈 请在左侧面板选择操作模式并配置参数
            """)

def main():
    """主函数"""
    app = StreamlitTokenFlowApp()
    app.run()

if __name__ == "__main__":
    main()
