import requests
import json
import time
import yaml
import os
from datetime import datetime
from pathlib import Path
import urllib3
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

# 禁用SSL警告
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

class SolscanCrawler:
    def __init__(self, config_path="settings/config.yaml"):
        self.config = self._load_config(config_path)
        self.base_url = self.config['api']['base_url']
        self.session = requests.Session()
        
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
        
        # 设置请求头
        self.headers = self._build_headers()
        
        # 设置cookies
        self.cookies = self._build_cookies()
        
        self.session.headers.update(self.headers)
        self.session.cookies.update(self.cookies)
        if self.proxies:
            self.session.proxies.update(self.proxies)
        
        # 设置超时时间
        self.timeout = self.config['api']['timeout']
    
    def _load_config(self, config_path):
        """加载配置文件"""
        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                return yaml.safe_load(f)
        except FileNotFoundError:
            print(f"配置文件 {config_path} 未找到")
            raise
        except yaml.YAMLError as e:
            print(f"配置文件格式错误: {e}")
            raise
    
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
    
    def get_token_transfers(self, address, page=1, page_size=None, from_time=None, to_time=None, value_filter=None):
        """
        获取代币转账记录
        
        Args:
            address: 代币地址
            page: 页码
            page_size: 每页大小 (如果未指定，使用配置文件默认值)
            from_time: 开始时间戳
            to_time: 结束时间戳
            value_filter: 值筛选
        """
        url = f"{self.base_url}/v2/token/transfer"
        
        # 使用配置文件中的默认参数
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
            
        try:
            print(f"正在请求: {url}")
            print(f"参数: {params}")
            if self.proxies:
                print(f"使用代理: {self.proxies}")
            
            response = self.session.get(url, params=params, timeout=self.timeout, verify=False)
            
            print(f"状态码: {response.status_code}")
            print(f"响应头: {dict(response.headers)}")
            
            if response.status_code == 200:
                data = response.json()
                print("请求成功!")
                return data
            elif response.status_code == 304:
                print("数据未修改 (304)")
                return {"message": "数据未修改", "status": 304}
            else:
                print(f"请求失败: {response.status_code}")
                print(f"响应内容: {response.text}")
                return None
                
        except Exception as e:
            print(f"请求出错: {str(e)}")
            return None
    
    def get_all_token_transfers(self, address, from_time=None, to_time=None, value_filter=None, max_pages=None):
        """
        获取所有代币转账记录，自动翻页直到没有更多数据
        
        Args:
            address: 代币地址
            from_time: 开始时间戳
            to_time: 结束时间戳
            value_filter: 值筛选
            max_pages: 最大页数限制（优先级高于配置文件）
        
        Returns:
            dict: 包含所有数据的汇总结果
        """
        all_data = []
        all_metadata = {}
        page = 1
        total_records = 0
        failed_pages = []
        
        # 获取翻页配置
        pagination_config = self.config.get('pagination', {})
        max_pages = max_pages or pagination_config.get('max_pages', 100)
        delay_between_pages = pagination_config.get('delay_between_pages', 0.5)
        retry_failed_pages = pagination_config.get('retry_failed_pages', 2)
        
        print("🚀 开始批量爬取数据...")
        print(f"📄 最大页数: {max_pages}")
        print(f"⏱️  页面延迟: {delay_between_pages}秒")
        
        while page <= max_pages:
            print(f"\n📖 正在爬取第 {page} 页...")
            
            # 重试机制
            page_data = None
            for retry in range(retry_failed_pages + 1):
                if retry > 0:
                    print(f"� 第 {page} 页重试 {retry}/{retry_failed_pages}...")
                    time.sleep(delay_between_pages * 2)  # 重试时延迟更久
                
                # 获取当前页数据
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
                print(f"❌ 第 {page} 页获取失败（已重试 {retry_failed_pages} 次）")
                failed_pages.append(page)
                page += 1
                continue
            
            # 检查是否有数据
            if 'data' not in page_data or not page_data['data']:
                print(f"✅ 第 {page} 页没有更多数据，爬取完成")
                break
            
            # 累积数据
            current_page_count = len(page_data['data'])
            all_data.extend(page_data['data'])
            total_records += current_page_count
            
            # 保存元数据（使用最新的）
            if 'metadata' in page_data:
                all_metadata = page_data['metadata']
            
            print(f"✅ 第 {page} 页获取成功，本页 {current_page_count} 条记录，总计 {total_records} 条")
            
            # 检查是否为最后一页（数据量少于默认页大小）
            default_page_size = self.config['default_params']['page_size']
            if current_page_count < default_page_size:
                print(f"📄 第 {page} 页数据量 ({current_page_count}) 小于页大小 ({default_page_size})，可能是最后一页")
                break
            
            page += 1
            
            # 添加延迟避免请求过快
            if page <= max_pages:
                time.sleep(delay_between_pages)
        
        # 构建最终结果
        result = {
            "success": True,
            "total_pages": page - 1,
            "total_records": total_records,
            "failed_pages": failed_pages,
            "data": all_data,
            "metadata": all_metadata,
            "crawl_info": {
                "start_time": datetime.now().isoformat(),
                "address": address,
                "from_time": from_time,
                "to_time": to_time,
                "value_filter": value_filter,
                "max_pages_limit": max_pages,
                "actual_pages": page - 1
            }
        }
        
        print(f"\n🎉 爬取完成！")
        print(f"📊 总计爬取 {page-1} 页，{total_records} 条记录")
        if failed_pages:
            print(f"⚠️ 失败页面: {failed_pages}")
        
        return result

    def save_to_file(self, data, filename=None):
        """保存数据到文件"""
        if not filename:
            storage_config = self.config['storage']
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename_template = storage_config['filename_format']
            filename = os.path.join(
                storage_config['directory'], 
                filename_template.format(timestamp=timestamp)
            )
        
        # 确保存储目录存在
        os.makedirs(os.path.dirname(filename), exist_ok=True)
        
        try:
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            print(f"数据已保存到: {filename}")
            return filename
        except Exception as e:
            print(f"保存文件失败: {str(e)}")
            return None

def main():
    # 创建爬虫实例
    crawler = SolscanCrawler()
    
    # 从配置文件获取目标代币信息
    target_tokens = crawler.config.get('target_tokens', [])
    if not target_tokens:
        print("配置文件中未找到目标代币，使用默认配置")
        # 使用原来的硬编码参数作为备选
        address = "5zCETicUCJqJ5Z3wbfFPZqtSpHPYqnggs1wX7ZRpump"
        token_name = "SPARK"
    else:
        # 使用配置文件中的第一个代币
        token_info = target_tokens[0]
        address = token_info['address']
        token_name = token_info.get('name', 'Unknown')
    
    # 查询参数
    from_time = 1756544400
    to_time = 1756548000
    value_filter = 30
    
    # 从配置文件获取最大页数，如果没有配置则使用默认值
    max_pages = crawler.config.get('pagination', {}).get('max_pages', 100)
    
    print("🎯 开始爬取 Solscan 数据...")
    print(f"📍 代币地址: {address}")
    print(f"🏷️  代币名称: {token_name}")
    print(f"⏰ 时间范围: {from_time} - {to_time}")
    print(f"💰 值筛选: >= ${value_filter}")
    print(f"📄 最大页数: {max_pages}")
    print("=" * 60)
    
    # 获取所有数据
    all_data = crawler.get_all_token_transfers(
        address=address,
        from_time=from_time,
        to_time=to_time,
        value_filter=value_filter
    )
    
    if all_data and all_data.get('total_records', 0) > 0:
        print("\n" + "="*60)
        print("📊 爬取统计信息:")
        print("="*60)
        print(f"📄 总页数: {all_data['total_pages']}")
        print(f"📝 总记录数: {all_data['total_records']}")
        print(f"📍 代币地址: {all_data['crawl_info']['address']}")
        print(f"⏰ 爬取时间: {all_data['crawl_info']['start_time']}")
        print(f"🎯 实际页数: {all_data['crawl_info']['actual_pages']}")
        
        if all_data.get('failed_pages'):
            print(f"⚠️ 失败页面: {all_data['failed_pages']}")
        
        # 显示前几条数据作为预览
        print(f"\n📋 数据预览 (前5条):")
        print("-" * 40)
        for i, record in enumerate(all_data['data'][:5]):
            print(f"{i+1}. 交易ID: {record.get('trans_id', 'N/A')[:20]}...")
            print(f"   金额: {record.get('amount', 0):,}")
            print(f"   价值: ${record.get('value', 0):.2f}")
            print(f"   时间: {record.get('block_time', 'N/A')}")
            print()
        
        # 保存数据
        print("💾 正在保存数据...")
        saved_file = crawler.save_to_file(all_data)
        if saved_file:
            print(f"\n✅ 数据已成功保存到: {saved_file}")
            print(f"📊 文件包含 {all_data['total_records']} 条记录")
        else:
            print("❌ 数据保存失败")
    else:
        print("❌ 未能获取到任何数据")

if __name__ == "__main__":
    main()
