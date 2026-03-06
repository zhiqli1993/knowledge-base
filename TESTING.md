# Knowledge Base 测试指南

## 前置条件检查

### 1. 验证 Ollama 和模型
```bash
# 检查 Ollama 是否安装
ollama --version

# 检查 nomic-embed-text 模型
ollama list | grep nomic

# 如果模型不存在，拉取它
ollama pull nomic-embed-text

# 启动 Ollama 服务
ollama serve
```

### 2. 验证配置文件
```bash
# 检查 knowledge base 配置
cat ~/.config/knowledge-base/config.json

# 检查项目 MCP 配置
cat /Users/zhiqli/knowledge-base/.mcp.json
```

### 3. 测试 MCP Server 启动
```bash
cd /Users/zhiqli/knowledge-base

# 测试服务器可以创建
python3 -c "from mcp_server.server import create_server; s = create_server(); print(f'✅ Server {s.name} created')"

# 测试异步初始化
python3 << 'PYEOF'
import asyncio
from mcp_server.server import create_server

async def test():
    server = create_server()
    tools = await server.list_tools()
    print(f"✅ {len(tools)} tools registered:")
    for t in tools:
        print(f"  - {t.name}")

asyncio.run(test())
PYEOF
```

## 在 Claude Code 中测试

### 1. 启动新会话
需要重启 Claude Code 以加载 `.mcp.json` 配置：
```bash
# 退出当前 Claude Code 会话
# 然后在 /Users/zhiqli/knowledge-base 目录重新启动
claude
```

### 2. 验证 MCP Server 已加载
在 Claude Code 中检查 MCP server 是否已加载。应该看到 `knowledge-base` 服务器。

### 3. 测试基本功能

#### 测试 1: 查看状态
```
/kb-status
```

应该看到：
```
Knowledge Base Status:

Sources:
  Total: 0
  Indexed: 0
  ...
```

#### 测试 2: 添加测试网页
```
/kb-add-url https://docs.python.org/3/library/asyncio.html
```

应该看到：
```
Added https://docs.python.org/3/library/asyncio.html to knowledge base. Indexing started in background.
```

#### 测试 3: 等待索引完成后搜索
等待几秒让索引完成，然后：
```
/kb-search asyncio event loop
```

应该看到搜索结果，包含来自 Python asyncio 文档的内容。

#### 测试 4: 列出来源
```
/kb-list
```

应该看到刚才添加的 URL。

#### 测试 5: 添加 GitHub 仓库（小型仓库测试）
```
/kb-add-repo anthropics/anthropic-quickstarts
```

等待索引完成后搜索：
```
/kb-search how to use claude api
```

#### 测试 6: 删除来源
```
/kb-delete web:docs.python.org/3/library/asyncio.html
```

## 故障排查

### MCP Server 未出现
1. 检查 `.mcp.json` 格式是否正确
2. 确保在项目根目录启动 Claude Code
3. 重启 Claude Code

### 索引失败
1. 确认 Ollama 正在运行：`curl http://localhost:11434/api/tags`
2. 检查日志（如果有）
3. 验证网络连接

### 搜索无结果
1. 确认索引已完成（使用 `/kb-status` 检查）
2. 尝试更具体的搜索查询
3. 检查是否有内容被实际索引了

## 性能基准

### 预期性能
- **Web页面索引**: 5-10 秒
- **小型 GitHub repo** (< 50 文件): 30-60 秒
- **中型 GitHub repo** (100-200 文件): 2-5 分钟

### 限制
- GitHub 文件大小限制: 5MB
- 网站最大页面数: 100
- 分块大小: 1000 字符（重叠 200）

## 清理测试数据

```bash
# 删除所有索引数据
rm -rf ~/.local/share/knowledge-base/

# 删除配置（可选）
rm -rf ~/.config/knowledge-base/

# 重新创建配置
mkdir -p ~/.config/knowledge-base
# 然后复制配置文件...
```
