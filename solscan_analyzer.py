#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Solscan Token Flow Analysis Tool
一体化代币流动分析工具

功能包括：
1. Solscan API 数据爬取
2. 自动 cf_clearance 更新
3. 数据分析和转换
4. 智能防护绕过

作者: LeviathanSunset
版本: 2.0.0
"""

import requests
import json
import time
import yaml
import os
import pandas as pd
from datetime import datetime
from pathlib import Path
import urllib3
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

# 禁用SSL警告
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

class SolscanAnalyzer:
    """Solscan 代币流动分析器 - 一体化工具"""
    
    def __init__(self, config_path="settings/config.yaml"):
        self.config_path = config_path
        self.config = self._load_config(config_path)
        self.base_url = self.config['api']['base_url']
        self.session = requests.Session()
        self.cf_clearance_updated = False
        
        # 设置代理
        if self.config['proxy']['enabled']:
            self.proxies = {
                'http': self.config['proxy']['http'],
                'https': self.config['proxy']['https']
            }
        else:
            self.proxies = {}
        
        # 设置重试策略
        retry_config = self.config['retry']
        retry_strategy = Retry(
            total=retry_config['max_retries'],
            backoff_factor=retry_config['backoff_factor'],
            status_forcelist=retry_config['status_codes'],
        )
        adapter = HTTPAdapter(max_retries=retry_strategy)
        self.session.mount("http://", adapter)
        self.session.mount("https://", adapter)
        
        # 设置请求头和cookies
        self.headers = self._build_headers()
        self.cookies = self._build_cookies()
        
        self.session.headers.update(self.headers)
        self.session.cookies.update(self.cookies)
        if self.proxies:
            self.session.proxies.update(self.proxies)
        
        self.timeout = self.config['api']['timeout']
        
        print("🚀 Solscan 代币流动分析器已初始化")
        print(f"🔧 代理状态: {'启用' if self.config['proxy']['enabled'] else '禁用'}")
        print(f"🛡️ 自动更新: 启用")
    
    def _load_config(self, config_path):
        """加载配置文件"""
        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                return yaml.safe_load(f)
        except FileNotFoundError:
            print(f"❌ 配置文件 {config_path} 未找到")
            raise
        except yaml.YAMLError as e:
            print(f"❌ 配置文件格式错误: {e}")
            raise
    
    def _save_config(self):
        """保存配置文件"""
        try:
            with open(self.config_path, 'w', encoding='utf-8') as f:
                yaml.dump(self.config, f, default_flow_style=False, allow_unicode=True)
            return True
        except Exception as e:
            print(f"❌ 保存配置文件失败: {e}")
            return False
    
    def _build_headers(self):
        """构建请求头"""
        headers_config = self.config['headers']
        return {
            'accept': headers_config['accept'],
            'accept-encoding': headers_config['accept_encoding'],
            'accept-language': headers_config['accept_language'],
            'origin': headers_config['origin'],
            'referer': headers_config['referer'],
            'sec-ch-ua': headers_config['sec_ch_ua'],
            'sec-ch-ua-mobile': headers_config['sec_ch_ua_mobile'],
            'sec-ch-ua-platform': headers_config['sec_ch_ua_platform'],
            'sec-fetch-dest': headers_config['sec_fetch_dest'],
            'sec-fetch-mode': headers_config['sec_fetch_mode'],
            'sec-fetch-site': headers_config['sec_fetch_site'],
            'user-agent': headers_config['user_agent']
        }
    
    def _build_cookies(self):
        """构建cookies"""
        cookies_config = self.config['cookies']
        return {
            '_ga': cookies_config['_ga'],
            'auth-token': cookies_config['auth_token'],
            'cf_clearance': cookies_config['cf_clearance'],
            '_ga_PS3V7B7KV0': cookies_config['_ga_PS3V7B7KV0']
        }
    
    def _update_cf_clearance_with_selenium(self):
        """使用 Selenium 自动获取新的 cf_clearance"""
        try:
            import undetected_chromedriver as uc
            from selenium.webdriver.support.ui import WebDriverWait
            
            print("🔄 启动浏览器获取新的 cf_clearance...")
            
            # 配置浏览器选项
            options = uc.ChromeOptions()
            
            if self.config['proxy']['enabled']:
                proxy = self.config['proxy']['http'].replace('http://', '')
                options.add_argument(f'--proxy-server={proxy}')
            
            options.add_argument('--disable-blink-features=AutomationControlled')
            options.add_argument('--disable-dev-shm-usage')
            options.add_argument('--no-sandbox')
            options.add_argument('--disable-gpu')
            
            # 创建浏览器实例
            driver = uc.Chrome(options=options)
            
            try:
                # 访问 solscan.io
                print("🌐 正在访问 solscan.io...")
                driver.get("https://solscan.io/")
                
                # 等待页面加载完成
                print("⏳ 等待 Cloudflare 验证通过...")
                wait = WebDriverWait(driver, 60)
                wait.until(lambda driver: "solscan" in driver.title.lower())
                time.sleep(5)
                
                # 获取 cookies
                cookies = driver.get_cookies()
                cf_clearance = None
                other_cookies = {}
                
                for cookie in cookies:
                    if cookie['name'] == 'cf_clearance':
                        cf_clearance = cookie['value']
                    elif cookie['name'] in ['_ga', '_ga_PS3V7B7KV0']:
                        other_cookies[cookie['name']] = cookie['value']
                
                if cf_clearance:
                    # 更新配置
                    self.config['cookies']['cf_clearance'] = cf_clearance
                    for name, value in other_cookies.items():
                        if name in self.config['cookies']:
                            self.config['cookies'][name] = value
                    
                    self._save_config()
                    
                    # 更新当前会话
                    self.cookies['cf_clearance'] = cf_clearance
                    self.session.cookies.update({'cf_clearance': cf_clearance})
                    for name, value in other_cookies.items():
                        if name in self.cookies:
                            self.cookies[name] = value
                            self.session.cookies.update({name: value})
                    
                    self.cf_clearance_updated = True
                    print(f"✅ cf_clearance 已更新: {cf_clearance[:50]}...")
                    return True
                else:
                    print("❌ 未获取到 cf_clearance")
                    return False
                    
            finally:
                driver.quit()
                
        except ImportError:
            print("❌ 需要安装依赖: pip install undetected-chromedriver selenium")
            return False
        except Exception as e:
            print(f"❌ Selenium 更新失败: {str(e)}")
            return False
    
    def _update_cf_clearance_with_requests(self):
        """使用 HTTP 请求尝试获取新的 cf_clearance"""
        try:
            print("🔄 尝试 HTTP 方式获取 cf_clearance...")
            
            temp_session = requests.Session()
            temp_session.headers.update({
                'User-Agent': self.config['headers']['user_agent'],
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
                'Accept-Language': 'en-US,en;q=0.5',
                'Accept-Encoding': 'gzip, deflate',
                'Connection': 'keep-alive',
            })
            
            if self.proxies:
                temp_session.proxies.update(self.proxies)
            
            response = temp_session.get("https://solscan.io/", timeout=30, verify=False)
            
            if 'cf_clearance' in temp_session.cookies:
                new_cf_clearance = temp_session.cookies['cf_clearance']
                
                self.config['cookies']['cf_clearance'] = new_cf_clearance
                self._save_config()
                
                self.cookies['cf_clearance'] = new_cf_clearance
                self.session.cookies.update({'cf_clearance': new_cf_clearance})
                
                self.cf_clearance_updated = True
                print(f"✅ HTTP 方式更新成功: {new_cf_clearance[:50]}...")
                return True
            else:
                print("❌ HTTP 方式无法获取 cf_clearance")
                return False
                
        except Exception as e:
            print(f"❌ HTTP 更新失败: {str(e)}")
            return False
    
    def _handle_cloudflare_challenge(self, response):
        """处理 Cloudflare 挑战"""
        if response.status_code == 403 or "cloudflare" in response.text.lower():
            print("🛡️ 检测到 Cloudflare 防护，开始自动更新...")
            
            # 尝试 Selenium 方式
            if self._update_cf_clearance_with_selenium():
                return True
            
            # 尝试 HTTP 方式
            if self._update_cf_clearance_with_requests():
                return True
            
            print("❌ 所有自动更新方式都失败，请检查网络或手动更新")
            return False
        
        return True
    
    def get_token_transfers(self, address, page=1, page_size=None, from_time=None, to_time=None, value_filter=None):
        """
        获取代币转账记录
        
        Args:
            address: 代币地址
            page: 页码
            page_size: 每页大小
            from_time: 开始时间戳
            to_time: 结束时间戳
            value_filter: 值筛选
        """
        url = f"{self.base_url}/v2/token/transfer"
        
        default_params = self.config['default_params']
        
        params = {
            'address': address,
            'page': page,
            'page_size': page_size or default_params['page_size'],
            'remove_spam': str(default_params['remove_spam']).lower(),
            'exclude_amount_zero': str(default_params['exclude_amount_zero']).lower()
        }
        
        if from_time:
            params['from_time'] = from_time
        if to_time:
            params['to_time'] = to_time
        if value_filter:
            params['value[]'] = value_filter
        
        max_retries = 2
        for attempt in range(max_retries + 1):
            try:
                print(f"📡 请求第 {page} 页数据 (尝试 {attempt + 1}/{max_retries + 1})")
                
                response = self.session.get(url, params=params, timeout=self.timeout, verify=False)
                
                # 检查 Cloudflare 挑战
                if response.status_code == 403 or (response.status_code != 200 and "cloudflare" in response.text.lower()):
                    if attempt < max_retries:
                        if self._handle_cloudflare_challenge(response):
                            print("🔄 cf_clearance 已更新，重试请求...")
                            continue
                        else:
                            return None
                    else:
                        print("❌ 已达到最大重试次数")
                        return None
                
                if response.status_code == 200:
                    data = response.json()
                    return data
                elif response.status_code == 304:
                    return {"message": "数据未修改", "status": 304}
                else:
                    print(f"❌ 请求失败: {response.status_code}")
                    if attempt < max_retries:
                        print("🔄 稍后重试...")
                        time.sleep(2)
                        continue
                    return None
                    
            except Exception as e:
                print(f"❌ 请求异常: {str(e)}")
                if attempt < max_retries:
                    print("🔄 稍后重试...")
                    time.sleep(2)
                    continue
                return None
        
        return None
    
    def crawl_all_data(self, address, from_time=None, to_time=None, value_filter=None, max_pages=None):
        """
        爬取所有代币转账数据
        
        Args:
            address: 代币地址
            from_time: 开始时间戳
            to_time: 结束时间戳
            value_filter: 值筛选
            max_pages: 最大页数
        
        Returns:
            dict: 包含所有数据的结果
        """
        all_data = []
        all_metadata = {}
        page = 1
        total_records = 0
        failed_pages = []
        
        # 获取配置
        pagination_config = self.config.get('pagination', {})
        max_pages = max_pages or pagination_config.get('max_pages', 100)
        delay_between_pages = pagination_config.get('delay_between_pages', 0.5)
        retry_failed_pages = pagination_config.get('retry_failed_pages', 2)
        
        print("🚀 开始批量爬取数据...")
        print(f"📄 最大页数: {max_pages}")
        print(f"⏱️  页面延迟: {delay_between_pages}秒")
        
        start_time = datetime.now()
        
        while page <= max_pages:
            print(f"\n📖 正在爬取第 {page} 页...")
            
            # 重试机制
            page_data = None
            for retry in range(retry_failed_pages + 1):
                if retry > 0:
                    print(f"🔄 第 {page} 页重试 {retry}/{retry_failed_pages}...")
                    time.sleep(delay_between_pages * 2)
                
                page_data = self.get_token_transfers(
                    address=address,
                    page=page,
                    from_time=from_time,
                    to_time=to_time,
                    value_filter=value_filter
                )
                
                if page_data:
                    break
            
            if not page_data:
                print(f"❌ 第 {page} 页获取失败")
                failed_pages.append(page)
                page += 1
                continue
            
            # 检查数据
            if 'data' not in page_data or not page_data['data']:
                print(f"✅ 第 {page} 页无更多数据，爬取完成")
                break
            
            # 累积数据
            current_page_count = len(page_data['data'])
            all_data.extend(page_data['data'])
            total_records += current_page_count
            
            if 'metadata' in page_data:
                all_metadata = page_data['metadata']
            
            print(f"✅ 第 {page} 页成功，本页 {current_page_count} 条，总计 {total_records} 条")
            
            # 检查是否最后一页
            default_page_size = self.config['default_params']['page_size']
            if current_page_count < default_page_size:
                print(f"📄 数据量小于页大小，可能是最后一页")
                page += 1
                break
            
            page += 1
            
            # 延迟
            if page <= max_pages:
                time.sleep(delay_between_pages)
        
        end_time = datetime.now()
        duration = (end_time - start_time).total_seconds()
        
        # 构建结果
        result = {
            "success": True,
            "total_pages": page - 1,
            "total_records": total_records,
            "failed_pages": failed_pages,
            "data": all_data,
            "metadata": all_metadata,
            "crawl_info": {
                "start_time": start_time.isoformat(),
                "end_time": end_time.isoformat(),
                "duration_seconds": duration,
                "address": address,
                "from_time": from_time,
                "to_time": to_time,
                "value_filter": value_filter,
                "max_pages_limit": max_pages,
                "actual_pages": page - 1,
                "cf_clearance_updated": self.cf_clearance_updated
            }
        }
        
        print(f"\n🎉 爬取完成！")
        print(f"📊 总计: {page - 1} 页, {total_records} 条记录")
        print(f"⏱️  耗时: {duration:.2f} 秒")
        if failed_pages:
            print(f"⚠️ 失败页面: {failed_pages}")
        if self.cf_clearance_updated:
            print("🔄 本次爬取中 cf_clearance 已自动更新")
        
        return result
    
    def analyze_data(self, data):
        """
        分析代币转账数据
        
        Args:
            data: 爬取的原始数据
            
        Returns:
            dict: 分析结果
        """
        if not data or not data.get('data'):
            print("❌ 没有数据可分析")
            return None
        
        print("\n📊 开始分析数据...")
        
        # 转换为 DataFrame
        df = pd.DataFrame(data['data'])
        
        # 基础统计
        total_transactions = len(df)
        
        # 金额统计
        if 'amount' in df.columns:
            df['amount'] = pd.to_numeric(df['amount'], errors='coerce')
            total_amount = df['amount'].sum()
            avg_amount = df['amount'].mean()
            median_amount = df['amount'].median()
            max_amount = df['amount'].max()
            min_amount = df['amount'].min()
        else:
            total_amount = avg_amount = median_amount = max_amount = min_amount = 0
        
        # 价值统计
        if 'value' in df.columns:
            df['value'] = pd.to_numeric(df['value'], errors='coerce')
            total_value = df['value'].sum()
            avg_value = df['value'].mean()
            median_value = df['value'].median()
            max_value = df['value'].max()
            min_value = df['value'].min()
        else:
            total_value = avg_value = median_value = max_value = min_value = 0
        
        # 时间分析
        if 'block_time' in df.columns:
            df['block_time'] = pd.to_datetime(df['block_time'], unit='s', errors='coerce')
            time_range = {
                'start': df['block_time'].min(),
                'end': df['block_time'].max(),
                'span_hours': (df['block_time'].max() - df['block_time'].min()).total_seconds() / 3600
            }
        else:
            time_range = None
        
        # 地址分析
        unique_from = df['from'].nunique() if 'from' in df.columns else 0
        unique_to = df['to'].nunique() if 'to' in df.columns else 0
        
        # 构建分析结果
        analysis = {
            "summary": {
                "total_transactions": total_transactions,
                "unique_from_addresses": unique_from,
                "unique_to_addresses": unique_to,
                "analysis_time": datetime.now().isoformat()
            },
            "amount_stats": {
                "total": total_amount,
                "average": avg_amount,
                "median": median_amount,
                "max": max_amount,
                "min": min_amount
            },
            "value_stats": {
                "total_usd": total_value,
                "average_usd": avg_value,
                "median_usd": median_value,
                "max_usd": max_value,
                "min_usd": min_value
            },
            "time_analysis": time_range,
            "raw_data_info": {
                "total_pages": data.get('total_pages', 0),
                "crawl_duration": data.get('crawl_info', {}).get('duration_seconds', 0),
                "cf_updated": data.get('crawl_info', {}).get('cf_clearance_updated', False)
            }
        }
        
        # 打印分析结果
        print("="*60)
        print("📈 数据分析结果")
        print("="*60)
        print(f"📝 总交易数: {total_transactions:,}")
        print(f"📤 唯一发送地址: {unique_from:,}")
        print(f"📥 唯一接收地址: {unique_to:,}")
        print(f"💰 总代币数量: {total_amount:,.2f}")
        print(f"💵 总价值: ${total_value:,.2f}")
        print(f"📊 平均交易价值: ${avg_value:.2f}")
        print(f"📊 中位数交易价值: ${median_value:.2f}")
        
        if time_range:
            print(f"⏰ 时间跨度: {time_range['span_hours']:.2f} 小时")
            print(f"🕐 开始时间: {time_range['start']}")
            print(f"🕐 结束时间: {time_range['end']}")
        
        return analysis
    
    def save_data(self, data, filename=None, include_analysis=True):
        """
        保存数据到文件
        
        Args:
            data: 要保存的数据
            filename: 文件名（可选）
            include_analysis: 是否包含分析结果
            
        Returns:
            str: 保存的文件路径
        """
        if not filename:
            storage_config = self.config['storage']
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename_template = storage_config['filename_format']
            filename = os.path.join(
                storage_config['directory'], 
                filename_template.format(timestamp=timestamp)
            )
        
        # 确保目录存在
        os.makedirs(os.path.dirname(filename), exist_ok=True)
        
        try:
            # 如果需要包含分析结果
            if include_analysis and data.get('data'):
                analysis = self.analyze_data(data)
                if analysis:
                    data['analysis'] = analysis
            
            # 保存 JSON 文件
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2, default=str)
            
            print(f"✅ 数据已保存到: {filename}")
            
            # 同时保存 CSV 格式（如果有数据）
            if data.get('data'):
                csv_filename = filename.replace('.json', '.csv')
                df = pd.DataFrame(data['data'])
                df.to_csv(csv_filename, index=False, encoding='utf-8-sig')
                print(f"✅ CSV 格式已保存到: {csv_filename}")
            
            return filename
            
        except Exception as e:
            print(f"❌ 保存失败: {str(e)}")
            return None
    
    def run_analysis(self, token_address=None, from_time=None, to_time=None, value_filter=None, max_pages=None):
        """
        运行完整的分析流程
        
        Args:
            token_address: 代币地址（可选，使用配置文件中的默认值）
            from_time: 开始时间戳
            to_time: 结束时间戳
            value_filter: 值筛选
            max_pages: 最大页数
        """
        # 获取代币信息
        if not token_address:
            target_tokens = self.config.get('target_tokens', [])
            if target_tokens:
                token_info = target_tokens[0]
                token_address = token_info['address']
                token_name = token_info.get('name', 'Unknown')
                token_symbol = token_info.get('symbol', 'Unknown')
            else:
                print("❌ 未指定代币地址且配置文件中无默认代币")
                return None
        else:
            token_name = "Custom"
            token_symbol = "Custom"
        
        print("🎯 开始代币流动分析...")
        print(f"📍 代币地址: {token_address}")
        print(f"🏷️  代币名称: {token_name}")
        print(f"🔤 代币符号: {token_symbol}")
        if from_time:
            print(f"⏰ 开始时间: {datetime.fromtimestamp(from_time)}")
        if to_time:
            print(f"⏰ 结束时间: {datetime.fromtimestamp(to_time)}")
        if value_filter:
            print(f"💰 值筛选: >= ${value_filter}")
        print("=" * 60)
        
        # 爬取数据
        data = self.crawl_all_data(
            address=token_address,
            from_time=from_time,
            to_time=to_time,
            value_filter=value_filter,
            max_pages=max_pages
        )
        
        if not data or not data.get('total_records'):
            print("❌ 未能获取到数据")
            return None
        
        # 保存数据（包含分析）
        print("\n💾 正在保存数据和分析结果...")
        saved_file = self.save_data(data, include_analysis=True)
        
        if saved_file:
            print(f"\n🎉 分析完成！")
            print(f"📁 结果文件: {saved_file}")
            print(f"📊 数据记录: {data['total_records']:,} 条")
            print(f"⏱️  总耗时: {data['crawl_info'].get('duration_seconds', 0):.2f} 秒")
            
            return {
                'data': data,
                'file': saved_file,
                'success': True
            }
        else:
            print("❌ 保存失败")
            return None

def main():
    """主函数 - 运行完整的分析流程"""
    print("🌟 Solscan Token Flow Analyzer v2.0")
    print("=" * 60)
    
    try:
        # 创建分析器实例
        analyzer = SolscanAnalyzer()
        
        # 运行分析
        result = analyzer.run_analysis(
            # 可以在这里自定义参数
            from_time=1756544400,  # 可选
            to_time=1756548000,    # 可选
            value_filter=30,       # 可选
            max_pages=50          # 可选
        )
        
        if result and result['success']:
            print("\n🎊 所有任务完成！")
        else:
            print("\n❌ 分析失败")
            
    except KeyboardInterrupt:
        print("\n\n⏹️  用户中断操作")
    except Exception as e:
        print(f"\n❌ 程序异常: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
