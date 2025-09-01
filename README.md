# Solana 代币流动分析工具

一个用于爬取 Solscan API 数据并分析代币流动的完整工具套件。

## 功能特性

### 🕷️ 数据爬取 (crawler.py)
- **自动翻页爬取**: 支持自动翻页直到没有更多数据
- **代理支持**: 支持HTTP/HTTPS代理配置
- **重试机制**: 内置指数退避重试策略
- **配置驱动**: 所有参数可通过YAML配置文件管理
- **数据保存**: 自动保存为JSON格式，包含爬取元信息

### 📊 流动分析 (analysis.py)
- **净流入/流出分析**: 计算每个地址的代币净流动
- **多维度排行榜**: 
  - 净流入排行榜（大买家）
  - 净流出排行榜（大卖家）
  - 总流入排行榜（活跃接收方）
  - 总流出排行榜（活跃发送方）
- **详细报告**: 生成完整的JSON分析报告
- **统计摘要**: 提供关键指标和数据概览

## 快速开始

### 1. 环境要求
```bash
Python 3.7+
requests
PyYAML
```

### 2. 配置设置
编辑 `settings/config.yaml` 文件：
```yaml
api:
  base_url: "https://api.solscan.io"
  endpoint: "/v2/account/transfer"
  
parameters:
  address: "your_token_address"
  from_time: 1756547700
  to_time: 1756634100
  
proxy:
  http: "http://127.0.0.1:10808"
  https: "http://127.0.0.1:10808"
```

### 3. 数据爬取
```bash
# 使用配置文件自动爬取
python crawler.py

# 自动翻页直到没有更多数据
```

### 4. 流动分析
```bash
# 自动分析最新数据
python analysis.py

# 指定数据文件
python analysis.py storage/your_data.json

# 自定义显示数量
python analysis.py -l 50
```

## 项目结构

```
flow/
├── crawler.py              # 主爬虫脚本
├── analysis.py             # 流动分析脚本
├── settings/
│   └── config.yaml         # 配置文件
├── storage/                # 数据存储目录
│   ├── solscan_data_*.json # 爬取的原始数据
│   └── analysis_report_*.json # 分析报告
├── ANALYSIS_README.md      # 分析脚本使用说明
├── CONFIG_README.md        # 配置文件说明
└── README.md              # 项目说明
```

## 使用示例

### 数据爬取示例
```bash
python crawler.py
```
输出：
```
🚀 开始爬取 Solscan 数据...
📄 正在爬取第 1 页...
📄 正在爬取第 2 页...
📄 正在爬取第 3 页...
🎉 爬取完成！📊 总计爬取 3 页，378 条记录
```

### 流动分析示例
```bash
python analysis.py
```
输出关键信息：
- 📊 分析摘要：总交易记录、涉及地址数、总交易数量
- 📈 净流入排行榜：显示最大的买家地址
- 📉 净流出排行榜：显示最大的卖家地址
- 💰 流入排行榜：按总接收量排序
- 💸 流出排行榜：按总发送量排序

## 核心功能详解

### 爬虫功能
- **自动分页**: 从第1页开始，自动翻页直到API返回空数据
- **错误处理**: 内置重试机制，处理网络超时和API限制
- **数据完整性**: 保存爬取元信息，包括总页数、记录数、失败页面等
- **配置灵活性**: 支持时间范围、代币地址、分页大小等参数配置

### 分析功能
- **精确计算**: 基于代币原始数量计算，考虑代币精度
- **多维排行**: 提供4个不同维度的排行榜
- **统计洞察**: 计算净流入/流出地址数量、最大交易等关键指标
- **数据导出**: 生成详细的JSON报告，包含所有地址的完整数据

## 配置说明

详细配置选项请参考：
- [CONFIG_README.md](CONFIG_README.md) - 爬虫配置说明
- [ANALYSIS_README.md](ANALYSIS_README.md) - 分析脚本说明

## 注意事项

1. **API限制**: 请遵守Solscan API的使用限制
2. **代理配置**: 如需使用代理，请确保代理服务正常运行
3. **数据隐私**: 爬取的数据包含在.gitignore中，避免意外提交敏感信息
4. **时间格式**: 配置文件中的时间使用Unix时间戳格式

## 许可证

本项目仅供学习和研究使用。

## 贡献

欢迎提交Issue和Pull Request来改进项目。

---

**⚠️ 免责声明**: 本工具仅用于数据分析研究，请确保遵守相关API的使用条款和当地法律法规。
