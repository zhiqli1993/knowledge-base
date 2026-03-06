# Knowledge Base 使用指南

## 快速开始

### 1. 使用 CLI 工具

```bash
# 查看状态
python3 kb_cli.py status

# 添加网页到 knowledge base
python3 kb_cli.py add-url "https://docs.python.org/3/library/asyncio.html"

# 搜索内容
python3 kb_cli.py search "asyncio event loop"

# 列出所有来源
python3 kb_cli.py list

# 添加 GitHub 仓库
python3 kb_cli.py add-repo "anthropics/anthropic-sdk-python"

# 删除来源
python3 kb_cli.py delete "web:docs.python.org/3/library/asyncio.html"
```

### 2. 使用 Python API

```python
import asyncio
from pathlib import Path
from mcp_server.config import Config
from mcp_server.storage import Storage
from mcp_server.indexer import Indexer
from mcp_server.retriever import Retriever
from mcp_server.models import Source, SourceType, SourceStatus

async def main():
    # Load config
    config = Config.load_default()
    
    # Initialize components
    storage = Storage(config.chroma.persist_directory_expanded / "storage.db")
    await storage.init()
    
    indexer = Indexer(config)
    await indexer.initialize()
    
    retriever = Retriever(config)
    
    # Add and index a web page
    source = Source(
        id="web:example.com/page",
        type=SourceType.WEB_PAGE,
        url="https://example.com/page",
        status=SourceStatus.PENDING
    )
    
    await storage.add_source(source)
    await indexer.index_source(source)
    
    # Search
    results = await retriever.search("your query", n_results=5)
    for result in results:
        print(f"Score: {result.score:.3f}")
        print(f"Text: {result.text[:200]}...")
        print()

asyncio.run(main())
```

### 3. MCP Server 集成 (待完成)

MCP server 已实现，但 Claude Code 集成还需要进一步配置。

当前配置:
- `.mcp.json` 已创建
- 7 个 MCP 工具已注册
- Server 可以独立运行

## 测试结果

### ✅ 已测试功能

1. **Web 页面索引**
   - ✅ 内容提取 (trafilatura)
   - ✅ 智能分块
   - ✅ 向量嵌入 (Ollama)
   - ✅ 持久化存储 (ChromaDB)

2. **语义搜索**
   - ✅ 向量相似度计算
   - ✅ 结果排序
   - ✅ 分数归一化

3. **元数据管理**
   - ✅ SQLite 存储
   - ✅ 状态跟踪
   - ✅ 来源管理

### 📊 性能数据

- **索引速度**: ~5秒 (小型网页)
- **嵌入维度**: 768 (nomic-embed-text)
- **存储大小**: ~274 MB (模型) + ~1 KB/chunk (数据)

### 🧪 测试案例

```bash
# 测试 1: 添加并搜索 Python 文档
python3 kb_cli.py add-url "https://docs.python.org/3/library/asyncio.html"
python3 kb_cli.py search "asyncio library"
# ✅ 返回 3 个相关结果

# 测试 2: 查看状态
python3 kb_cli.py status
# ✅ 显示 1 个已索引来源

# 测试 3: 列出来源
python3 kb_cli.py list
# ✅ 显示来源详情
```

## 故障排查

### 搜索无结果

1. 确认 Ollama 正在运行:
   ```bash
   curl http://localhost:11434/api/tags
   ```

2. 检查 ChromaDB 中的数据:
   ```python
   from mcp_server.config import Config
   from mcp_server.chroma_client import ChromaClient
   
   config = Config.load_default()
   chroma = ChromaClient(config.chroma)
   print(f"Chunks: {chroma.count()}")
   ```

3. 验证索引状态:
   ```bash
   python3 kb_cli.py status
   ```

### 索引失败

1. 检查网络连接
2. 验证 URL 可访问
3. 查看错误日志

### ChromaDB 持久化问题

- 确保使用 `PersistentClient` 而非 `Client`
- 检查存储路径权限
- 验证磁盘空间

## 限制和已知问题

1. **GitHub 仓库索引**: 已实现但未充分测试
2. **网站 sitemap 索引**: 已实现但未充分测试
3. **MCP Server 集成**: 需要进一步配置
4. **搜索分数**: 当前较低 (0.003-0.006)，可能需要调优

## 下一步

1. 完成 MCP Server 在 Claude Code 中的集成
2. 测试 GitHub 仓库索引
3. 测试网站 sitemap 索引
4. 优化搜索相关性评分
5. 添加更多测试用例
