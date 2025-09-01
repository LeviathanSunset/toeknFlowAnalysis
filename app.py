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
        if 'net_flows_df' not in st.session_state:
            st.session_state.net_flows_df = None
        if 'analysis_complete' not in st.session_state:
            st.session_state.analysis_complete = False
        if 'crawl_in_progress' not in st.session_state:
            st.session_state.crawl_in_progress = False
        if 'crawl_config' not in st.session_state:
            st.session_state.crawl_config = {
                'token_address': '5zCETicUCJqJ5Z3wbfFPZqtSpHPYqnggs1wX7ZRpump',
                'max_pages': 50,
                'value_filter': 30,
                'from_time': None,
                'to_time': None
            }
    
    def load_available_data_files(self):
        """获取可用的数据文件列表"""
        storage_dir = Path("storage")
        if not storage_dir.exists():
            return []
        
        # 查找JSON数据文件
        json_files = list(storage_dir.glob("solscan_data_*.json"))
        json_files.sort(key=lambda x: x.stat().st_mtime, reverse=True)
        
        return [str(f) for f in json_files]
    
    def crawl_new_data(self, config):
        """爬取新的代币数据"""
        try:
            # 初始化爬虫
            crawler = SolscanAnalyzer()
            
            # 设置进度显示
            progress_container = st.empty()
            status_container = st.empty()
            
            with progress_container.container():
                progress_bar = st.progress(0)
                
            status_container.info("🚀 正在初始化爬虫...")
            progress_bar.progress(10)
            
            # 开始爬取
            status_container.info(f"📡 正在爬取代币数据: {config['token_address'][:16]}...")
            progress_bar.progress(30)
            
            # 调用爬取方法
            result = crawler.crawl_all_data(
                address=config['token_address'],
                from_time=config.get('from_time'),
                to_time=config.get('to_time'),
                value_filter=config.get('value_filter'),
                max_pages=config.get('max_pages', 50)
            )
            
            progress_bar.progress(70)
            status_container.info("💾 正在保存数据...")
            
            if result and result.get('success'):
                # 保存数据
                saved_file = crawler.save_data(result, include_analysis=False)
                
                progress_bar.progress(100)
                status_container.success(f"✅ 爬取完成！获得 {result.get('total_records', 0)} 条记录")
                
                time.sleep(1)
                progress_container.empty()
                status_container.empty()
                
                return saved_file
            else:
                status_container.error("❌ 爬取失败")
                return None
                
        except Exception as e:
            st.error(f"爬取过程中出错: {str(e)}")
            return None
    
    def format_address(self, address, length=16):
        """格式化地址显示，优先显示标签名"""
        if pd.isna(address) or not address:
            return "N/A"
        
        # 检查是否有地址标签
        if hasattr(self.analyzer, 'address_labels') and address in self.analyzer.address_labels:
            label = self.analyzer.address_labels[address]
            if len(label) <= length + 5:  # 地址标签可以稍微长一点
                return label
            else:
                return label[:length] + "..."
        
        # 没有标签时显示缩短的地址
        if len(address) <= length:
            return address
        return f"{address[:length//2]}...{address[-length//2:]}"
    
    def format_currency(self, value):
        """格式化货币显示"""
        if pd.isna(value):
            return "$0.00"
        return f"${value:,.2f}"
    
    def format_tokens(self, value):
        """格式化代币数量显示"""
        if pd.isna(value):
            return "0"
        
        # 根据数量大小选择显示格式
        if abs(value) >= 1_000_000:
            return f"{value/1_000_000:,.2f}M"
        elif abs(value) >= 1_000:
            return f"{value/1_000:,.2f}K"
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
        
        # 分析参数
        st.sidebar.subheader("⚙️ 分析参数")
        
        top_n = st.sidebar.slider(
            "显示排行榜数量:",
            min_value=5,
            max_value=50,
            value=20,
            step=5,
            help="选择要显示的净流入/流出排行榜数量"
        )
        
        # 只在使用现有数据模式下显示价值过滤器（爬取模式已经有了）
        if operation_mode == "📂 使用现有数据":
            min_value_threshold = st.sidebar.number_input(
                "最小交易价值过滤 ($):",
                min_value=0.0,
                max_value=10000.0,
                value=0.0,
                step=10.0,
                help="分析时过滤掉小于此价值的交易"
            )
        else:
            # 爬取模式使用爬取时的价值过滤
            min_value_threshold = 0.0
        
        address_types = [
            "全部", "鲸鱼买入", "大买家", "活跃买家", "普通买家",
            "做市商/套利者", "普通卖家", "活跃卖家", "大卖家", "鲸鱼卖出"
        ]
        
        selected_types = st.sidebar.multiselect(
            "地址类型筛选:",
            options=address_types,
            default=["全部"],
            help="选择要显示的地址类型"
        )
        
        # 执行按钮
        st.sidebar.subheader("🎯 执行操作")
        
        if operation_mode == "📂 使用现有数据":
            analyze_button = st.sidebar.button(
                "🚀 开始分析",
                type="primary",
                use_container_width=True,
                help="分析选定的数据文件"
            )
            crawl_button = False
        else:
            crawl_button = st.sidebar.button(
                "🕸️ 爬取并分析",
                type="primary",
                use_container_width=True,
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
            'top_n': top_n,
            'min_value_threshold': min_value_threshold,
            'selected_types': selected_types,
            'analyze_button': analyze_button,
            'crawl_button': crawl_button
        }
        
        selected_types = st.sidebar.multiselect(
            "地址类型筛选:",
            options=address_types,
            default=["全部"],
            help="选择要显示的地址类型"
        )
        
        # 开始分析按钮
        analyze_button = st.sidebar.button(
            "🚀 开始分析",
            type="primary",
            use_container_width=True
        )
        
        return {
            'selected_file': selected_file,
            'top_n': top_n,
            'min_value_threshold': min_value_threshold,
            'selected_types': selected_types,
            'analyze_button': analyze_button
        }
    
    def load_and_analyze_data(self, file_path, min_value_threshold=0):
        """加载和分析数据"""
        try:
            # 显示进度
            progress_bar = st.progress(0)
            status_text = st.empty()
            
            # 初始化分析器
            status_text.text("正在初始化分析器...")
            progress_bar.progress(10)
            
            analyzer = TokenFlowAnalyzer()
            
            # 加载数据
            status_text.text(f"正在加载数据文件: {Path(file_path).name}...")
            progress_bar.progress(30)
            
            analyzer.load_data(file_path)
            
            # 应用价值过滤
            if min_value_threshold > 0:
                status_text.text(f"正在应用价值过滤 (>= ${min_value_threshold})...")
                progress_bar.progress(50)
                original_count = len(analyzer.df)
                analyzer.df = analyzer.df[analyzer.df['value'] >= min_value_threshold]
                filtered_count = len(analyzer.df)
                st.info(f"价值过滤: {original_count} → {filtered_count} 条记录")
            
            # 计算净流动
            status_text.text("正在计算净流入/流出...")
            progress_bar.progress(70)
            
            analyzer.calculate_net_flows()
            
            # 完成
            status_text.text("分析完成！")
            progress_bar.progress(100)
            
            time.sleep(0.5)
            progress_bar.empty()
            status_text.empty()
            
            return analyzer
            
        except Exception as e:
            st.error(f"数据加载失败: {str(e)}")
            return None
    
    def filter_data_by_types(self, df, selected_types):
        """根据地址类型筛选数据"""
        if "全部" in selected_types:
            return df
        return df[df['address_type'].isin(selected_types)]
    
    def render_summary_metrics(self, analyzer):
        """渲染汇总指标"""
        st.subheader("📊 总体概览")
        
        df = analyzer.net_flows_df
        
        # 计算指标（基于代币数量和美元价值）
        total_addresses = len(df)
        total_transactions = df['total_transactions'].sum()
        total_net_inflow_tokens = df[df['net_tokens'] > 0]['net_tokens'].sum()
        total_net_outflow_tokens = abs(df[df['net_tokens'] < 0]['net_tokens'].sum())
        total_net_inflow = df[df['net_value'] > 0]['net_value'].sum()
        total_net_outflow = abs(df[df['net_value'] < 0]['net_value'].sum())
        net_balance = total_net_inflow - total_net_outflow
        net_balance_tokens = total_net_inflow_tokens - total_net_outflow_tokens
        
        # 显示指标
        col1, col2, col3, col4, col5 = st.columns(5)
        
        with col1:
            st.metric(
                label="📍 总地址数",
                value=f"{total_addresses:,}",
                help="参与交易的唯一地址数量"
            )
        
        with col2:
            st.metric(
                label="📝 总交易数",
                value=f"{total_transactions:,}",
                help="所有地址的交易总数"
            )
        
        with col3:
            st.metric(
                label="🪙 总净流入(代币)",
                value=self.format_tokens(total_net_inflow_tokens),
                help="所有地址净流入的代币数量总和"
            )
        
        with col4:
            st.metric(
                label="🪙 总净流出(代币)",
                value=self.format_tokens(total_net_outflow_tokens),
                delta_color="inverse",
                help="所有地址净流出的代币数量总和"
            )
        
        with col5:
            st.metric(
                label="� 净平衡(美元)",
                value=self.format_currency(net_balance),
                delta=f"{'+' if net_balance >= 0 else ''}{net_balance/1000:.1f}K" if abs(net_balance) > 1000 else None,
                delta_color="normal" if net_balance >= 0 else "inverse",
                help="总净流入与总净流出的差额（美元价值）"
            )
    
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
                    y=top_inflows.head(10)['address'].apply(lambda x: self.format_address(x, 12)),
                    orientation='h',
                    color='address_type',
                    color_discrete_map={t: self.get_address_type_color(t) for t in top_inflows['address_type'].unique()},
                    title=f"前10名净流入地址（代币数量）",
                    labels={'net_tokens': '净流入 (代币)', 'y': '地址'}
                )
                fig_inflow.update_layout(height=400, yaxis={'categoryorder': 'total ascending'})
                st.plotly_chart(fig_inflow, use_container_width=True)
        
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
                    y=top_outflows_display['address'].apply(lambda x: self.format_address(x, 12)),
                    orientation='h',
                    color='address_type',
                    color_discrete_map={t: self.get_address_type_color(t) for t in top_outflows_display['address_type'].unique()},
                    title=f"前10名净流出地址（代币数量）",
                    labels={'net_outflow': '净流出 (代币)', 'y': '地址'}
                )
                fig_outflow.update_layout(height=400, yaxis={'categoryorder': 'total ascending'})
                st.plotly_chart(fig_outflow, use_container_width=True)
        
        # 地址类型分布饼图
        st.markdown("#### 🥧 地址类型分布")
        type_counts = df['address_type'].value_counts()
        
        fig_pie = px.pie(
            values=type_counts.values,
            names=type_counts.index,
            title="地址类型分布",
            color=type_counts.index,
            color_discrete_map={t: self.get_address_type_color(t) for t in type_counts.index}
        )
        fig_pie.update_layout(height=400)
        st.plotly_chart(fig_pie, use_container_width=True)
    
    def render_data_tables(self, analyzer, top_n=20, selected_types=["全部"]):
        """渲染数据表格"""
        st.subheader("📋 详细数据表")
        
        df = analyzer.net_flows_df
        
        # 应用类型筛选
        filtered_df = self.filter_data_by_types(df, selected_types)
        
        # 创建标签页
        tab1, tab2, tab3 = st.tabs(["🏆 净流入排行", "📉 净流出排行", "📊 全部数据"])
        
        with tab1:
            st.markdown("#### 净流入最大的地址 (代币数量)")
            top_inflows = filtered_df.nlargest(top_n, 'net_tokens')
            
            if not top_inflows.empty:
                # 格式化显示数据
                display_df = top_inflows.copy()
                display_df['排名'] = range(1, len(display_df) + 1)
                display_df['完整地址'] = display_df['address']  # 显示完整地址便于复制
                display_df['净流入(代币)'] = display_df['net_tokens'].apply(self.format_tokens)
                display_df['净流入(美元)'] = display_df['net_value'].apply(self.format_currency)
                display_df['流入(代币)'] = display_df['inflow_tokens'].apply(self.format_tokens)
                display_df['流出(代币)'] = display_df['outflow_tokens'].apply(self.format_tokens)
                display_df['交易数'] = display_df['total_transactions']
                display_df['类型'] = display_df['address_type']
                
                st.dataframe(
                    display_df[['排名', '完整地址', '净流入(代币)', '净流入(美元)', '流入(代币)', '流出(代币)', '交易数', '类型']],
                    use_container_width=True,
                    height=400
                )
            else:
                st.info("没有符合条件的净流入数据")
        
        with tab2:
            st.markdown("#### 净流出最大的地址 (代币数量)")
            top_outflows = filtered_df.nsmallest(top_n, 'net_tokens')
            
            if not top_outflows.empty:
                # 格式化显示数据
                display_df = top_outflows.copy()
                display_df['排名'] = range(1, len(display_df) + 1)
                display_df['完整地址'] = display_df['address']  # 显示完整地址便于复制
                display_df['净流出(代币)'] = display_df['net_tokens'].apply(lambda x: self.format_tokens(abs(x)))
                display_df['净流出(美元)'] = display_df['net_value'].apply(lambda x: self.format_currency(abs(x)))
                display_df['流入(代币)'] = display_df['inflow_tokens'].apply(self.format_tokens)
                display_df['流出(代币)'] = display_df['outflow_tokens'].apply(self.format_tokens)
                display_df['交易数'] = display_df['total_transactions']
                display_df['类型'] = display_df['address_type']
                
                st.dataframe(
                    display_df[['排名', '完整地址', '净流出(代币)', '净流出(美元)', '流入(代币)', '流出(代币)', '交易数', '类型']],
                    use_container_width=True,
                    height=400
                )
            else:
                st.info("没有符合条件的净流出数据")
        
        with tab3:
            st.markdown("#### 所有地址数据")
            
            # 搜索功能
            search_term = st.text_input("🔍 搜索地址:", placeholder="输入地址的部分字符进行搜索")
            
            display_data = filtered_df.copy()
            
            if search_term:
                display_data = display_data[display_data['address'].str.contains(search_term, case=False, na=False)]
            
            # 排序选项
            sort_options = {
                "净流入代币数（高到低）": ('net_tokens', False),
                "净流入代币数（低到高）": ('net_tokens', True),
                "净流入美元价值（高到低）": ('net_value', False),
                "净流入美元价值（低到高）": ('net_value', True),
                "交易数（高到低）": ('total_transactions', False),
                "流入代币数（高到低）": ('inflow_tokens', False),
                "流出代币数（高到低）": ('outflow_tokens', False)
            }
            
            sort_choice = st.selectbox("排序方式:", list(sort_options.keys()))
            sort_column, ascending = sort_options[sort_choice]
            
            display_data = display_data.sort_values(by=sort_column, ascending=ascending)
            
            if not display_data.empty:
                # 格式化显示
                display_df = display_data.copy()
                display_df['完整地址'] = display_df['address']  # 显示完整地址便于复制
                display_df['净流动(代币)'] = display_df['net_tokens'].apply(self.format_tokens)
                display_df['净流动(美元)'] = display_df['net_value'].apply(self.format_currency)
                display_df['流入(代币)'] = display_df['inflow_tokens'].apply(self.format_tokens)
                display_df['流出(代币)'] = display_df['outflow_tokens'].apply(self.format_tokens)
                display_df['交易数'] = display_df['total_transactions']
                display_df['类型'] = display_df['address_type']
                
                st.dataframe(
                    display_df[['完整地址', '净流动(代币)', '净流动(美元)', '流入(代币)', '流出(代币)', '交易数', '类型']],
                    use_container_width=True,
                    height=500
                )
                
                # 下载按钮
                csv = display_df.to_csv(index=False, encoding='utf-8-sig')
                st.download_button(
                    label="📥 下载CSV文件",
                    data=csv,
                    file_name=f"net_flow_analysis_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                    mime="text/csv"
                )
            else:
                st.info("没有符合条件的数据")
    
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
        
        # 处理爬取操作
        if sidebar_config['crawl_button']:
            st.session_state.crawl_in_progress = True
            st.session_state.analysis_complete = False
            
            st.info("🚀 开始爬取新数据...")
            
            # 爬取数据
            crawl_result = self.crawl_new_data(sidebar_config['crawl_config'])
            
            if crawl_result:
                st.success(f"✅ 数据爬取成功！文件保存为: {Path(crawl_result).name}")
                
                # 自动开始分析新爬取的数据
                st.info("🔄 正在分析新爬取的数据...")
                
                analyzer = self.load_and_analyze_data(
                    crawl_result,
                    sidebar_config['min_value_threshold']
                )
                
                if analyzer:
                    st.session_state.analyzer = analyzer
                    st.session_state.analysis_complete = True
                    st.success("✅ 数据分析完成！")
                else:
                    st.error("❌ 数据分析失败！")
            else:
                st.error("❌ 数据爬取失败！")
            
            st.session_state.crawl_in_progress = False
            st.rerun()
        
        # 处理分析操作（使用现有数据）
        elif sidebar_config['analyze_button'] or st.session_state.analysis_complete:
            
            # 加载和分析数据
            if sidebar_config['analyze_button'] or not st.session_state.analysis_complete:
                with st.spinner("正在分析数据..."):
                    analyzer = self.load_and_analyze_data(
                        sidebar_config['selected_file'],
                        sidebar_config['min_value_threshold']
                    )
                
                if analyzer:
                    st.session_state.analyzer = analyzer
                    st.session_state.analysis_complete = True
                    st.success("✅ 数据分析完成！")
                else:
                    st.error("❌ 数据分析失败！")
                    st.stop()
            
            analyzer = st.session_state.analyzer
            
            if analyzer and analyzer.net_flows_df is not None:
                # 渲染分析结果
                self.render_summary_metrics(analyzer)
                
                st.divider()
                
                self.render_flow_charts(analyzer, sidebar_config['top_n'])
                
                st.divider()
                
                self.render_data_tables(
                    analyzer,
                    sidebar_config['top_n'],
                    sidebar_config['selected_types']
                )
                
                # 页脚信息
                st.markdown("---")
                st.markdown("""
                <div style="text-align: center; color: #666; font-size: 0.9rem;">
                    🔍 Solscan代币流动分析平台 | 
                    📊 数据更新时间: {} | 
                    🛠️ 由 LeviathanSunset 开发
                </div>
                """.format(datetime.now().strftime("%Y-%m-%d %H:%M:%S")), unsafe_allow_html=True)
            
        else:
            # 初始状态页面
            st.info("👆 请在左侧面板选择操作模式并点击相应按钮")
            
            # 显示使用说明
            with st.expander("📖 使用说明", expanded=True):
                st.markdown("""
                ### 🚀 新功能：一键爬取和分析
                
                现在支持两种操作模式：
                
                #### 📂 使用现有数据
                1. **选择文件**: 从已有的数据文件中选择
                2. **设置参数**: 配置分析参数（排行榜数量、价值过滤等）
                3. **开始分析**: 点击 "🚀 开始分析" 按钮
                
                #### 🔄 爬取新数据
                1. **配置爬取**: 设置代币地址、页数限制、价值过滤等
                2. **时间范围**: 可选择特定时间段的数据
                3. **一键执行**: 点击 "🕸️ 爬取并分析" 按钮自动完成爬取和分析
                
                ### 🎯 核心功能：
                - 📊 **实时分析**: 计算每个地址的净流入和净流出
                - 🏆 **智能排行**: 显示净流入/流出最大的地址
                - 📈 **可视化**: 交互式图表展示数据分布
                - 🔍 **多重筛选**: 按地址类型和关键词筛选数据
                - 📥 **数据导出**: 支持CSV格式下载
                - 🕸️ **自动爬取**: 无需手动运行命令行工具
                
                ### 💡 使用技巧：
                - **时间过滤**: 启用时间范围可以分析特定时段的交易
                - **价值过滤**: 设置最小价值可以专注于大额交易
                - **地址类型**: 使用类型筛选快速找到鲸鱼或做市商
                """)
            
            # 显示系统状态
            with st.expander("⚙️ 系统状态"):
                data_files = self.load_available_data_files()
                st.write(f"📁 已有数据文件: {len(data_files)} 个")
                
                if data_files:
                    latest_file = data_files[0]
                    file_time = datetime.fromtimestamp(Path(latest_file).stat().st_mtime)
                    st.write(f"🕐 最新数据: {file_time.strftime('%Y-%m-%d %H:%M:%S')}")
                
                st.write(f"🔧 爬取状态: {'进行中' if st.session_state.crawl_in_progress else '空闲'}")
                st.write(f"📊 分析状态: {'已完成' if st.session_state.analysis_complete else '未开始'}")

def main():
    """主函数"""
    app = StreamlitTokenFlowApp()
    app.run()

if __name__ == "__main__":
    main()
