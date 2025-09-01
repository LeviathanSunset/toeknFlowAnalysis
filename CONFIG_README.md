# 配置文件使用说明

## 📋 Solscan 爬虫配置说明

这个 `config.yaml` 文件包含了 Solscan API 爬虫的所有重要配置参数。

### 🔧 主要配置项

#### API 配置
- `api.base_url`: Solscan API 的基础 URL
- `api.timeout`: 请求超时时间（秒）

#### 代理配置
- `proxy.enabled`: 是否启用代理
- `proxy.http/https`: HTTP/HTTPS 代理地址

#### 认证信息
- `cookies`: 包含认证令牌和会话信息
  - `auth_token`: JWT 认证令牌（需要定期更新）
  - `cf_clearance`: Cloudflare 验证令牌
  - `_ga`: Google Analytics cookies

#### 查询参数
- `default_params.page_size`: 默认每页数据量
- `default_params.remove_spam`: 是否移除垃圾数据
- `default_params.exclude_amount_zero`: 是否排除零金额转账

#### 目标代币
- `target_tokens`: 要爬取的代币列表，可以添加多个代币

### 🔄 更新配置

#### 更新认证信息
当 cookies 过期时，需要：
1. 在浏览器中重新访问 Solscan
2. 从开发者工具中获取新的 cookies
3. 更新配置文件中的相应字段

#### 添加新代币
在 `target_tokens` 部分添加新的代币配置：
```yaml
target_tokens:
  - address: "新代币地址"
    name: "代币名称"
    symbol: "代币符号"
    description: "代币描述"
```

#### 代理设置
如果不需要代理，将 `proxy.enabled` 设置为 `false`：
```yaml
proxy:
  enabled: false
```

### ⚠️ 注意事项

1. **敏感信息**: 配置文件包含认证信息，请妥善保管
2. **定期更新**: auth_token 和 cf_clearance 需要定期更新
3. **网络环境**: 根据实际网络环境调整代理设置
4. **备份配置**: 建议备份工作正常的配置文件

### 🚀 使用方式

```bash
# 使用默认配置文件
python crawler.py

# 如果配置文件位置不同，可以在代码中修改路径
# SolscanCrawler(config_path="custom/path/config.yaml")
```
