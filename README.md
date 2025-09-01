# Solscan Token Flow Analyzer v2.0

一体化代币流动分析工具，集成数据爬取、自动防护绕过、数据分析功能。

## ✨ 主要功能

- 🚀 **智能数据爬取** - 从 Solscan API 获取代币转账数据
- 🛡️ **自动防护绕过** - 智能检测并自动更新 cf_clearance，绕过 Cloudflare 防护
- 📊 **数据分析** - 自动分析交易数据，生成统计报告
- 💾 **多格式导出** - 支持 JSON 和 CSV 格式数据导出
- 🔄 **自动重试** - 智能重试机制，提高数据获取成功率
- ⚙️ **灵活配置** - 支持代理、参数自定义配置

## 🚀 快速开始

### 1. 安装依赖
```bash
pip install requests pyyaml pandas undetected-chromedriver selenium
```

### 2. 配置设置
编辑 `settings/config.yaml` 文件，配置代理、cookies 等参数。

### 3. 运行分析
```bash
python solscan_analyzer.py
```

## 📁 项目结构

```
toeknFlowAnalysis/
├── solscan_analyzer.py     # 🌟 主程序文件（一体化工具）
├── settings/
│   └── config.yaml         # ⚙️ 配置文件
├── storage/               # 📁 数据存储目录
├── README.md              # 📖 项目说明
└── CONFIG_README.md       # ⚙️ 配置说明
```

## 🎯 使用示例

### 基础使用
程序会自动使用配置文件中的默认代币进行分析：
```bash
python solscan_analyzer.py
```

### 自定义参数
你也可以修改 `main()` 函数中的参数：
```python
result = analyzer.run_analysis(
    token_address="your_token_address",  # 自定义代币地址
    from_time=1756544400,               # 开始时间戳
    to_time=1756548000,                 # 结束时间戳
    value_filter=30,                    # 最小交易价值($)
    max_pages=50                        # 最大爬取页数
)
```

## 📊 输出结果

程序会生成以下文件：
- `solscan_data_YYYYMMDD_HHMMSS.json` - 完整数据和分析结果
- `solscan_data_YYYYMMDD_HHMMSS.csv` - 交易数据表格

分析结果包括：
- 📈 交易统计（总数、金额、价值）
- 📍 地址分析（唯一发送/接收地址）
- ⏰ 时间分析（时间跨度、交易密度）
- 💰 价值分析（平均值、中位数、最大/最小值）

## 🛡️ 自动防护绕过

程序具备智能防护绕过能力：
- 自动检测 Cloudflare 阻拦
- 使用真实浏览器获取新的 cf_clearance
- 自动更新配置文件
- 无缝重试失败的请求

## ⚙️ 配置说明

详细配置说明请参考 `CONFIG_README.md`。

主要配置项：
- **API 设置** - 基础 URL、超时时间
- **代理配置** - HTTP/HTTPS 代理支持
- **请求头** - User-Agent、Accept 等
- **Cookies** - 包含 cf_clearance 等认证信息
- **重试策略** - 最大重试次数、退避策略
- **翻页设置** - 最大页数、延迟时间
- **目标代币** - 要分析的代币地址列表

## 🔧 高级功能

### 自定义分析器
```python
from solscan_analyzer import SolscanAnalyzer

# 创建分析器
analyzer = SolscanAnalyzer("path/to/config.yaml")

# 只爬取数据
data = analyzer.crawl_all_data(
    address="token_address",
    value_filter=100,
    max_pages=20
)

# 只分析数据
analysis = analyzer.analyze_data(data)

# 保存结果
analyzer.save_data(data, "custom_filename.json")
```

### 批量分析
```python
# 分析多个代币
tokens = [
    "5zCETicUCJqJ5Z3wbfFPZqtSpHPYqnggs1wX7ZRpump",
    "another_token_address"
]

for token in tokens:
    result = analyzer.run_analysis(token_address=token)
    print(f"Token {token}: {result['data']['total_records']} transactions")
```

## 🛠️ 故障排除

### 常见问题

1. **cf_clearance 过期**
   - 程序会自动检测并更新
   - 确保安装了 Chrome 浏览器

2. **代理连接失败**
   - 检查代理设置是否正确
   - 可以临时禁用代理测试

3. **数据获取失败**
   - 检查网络连接
   - 确认 Solscan API 可访问性

### 调试模式
```python
import logging
logging.basicConfig(level=logging.DEBUG)

# 然后运行分析器
analyzer = SolscanAnalyzer()
```

## 📊 性能特点

- **高效爬取** - 支持并发和智能延迟
- **内存优化** - 大数据集分批处理
- **断点续传** - 支持失败页面重试
- **实时监控** - 详细进度和状态显示

## 🤝 贡献

欢迎提交 Issue 和 Pull Request！

## 📄 许可证

MIT License

## 📝 更新日志

### v2.0.0 (Current)
- ✨ 全新一体化架构
- 🛡️ 集成自动 cf_clearance 更新
- 📊 内置数据分析功能
- 💾 支持多格式数据导出
- 🚀 优化性能和稳定性
- 🧹 精简项目结构，整合为单文件

### v1.x
- 基础爬虫功能
- 分离的分析工具
- 手动配置管理
