# Knowledge Base 使用指南

## 快速开始

### 1. 使用 CLI 工具

```bash
# 安装本地命令
pip install -e .

# 查看状态
kb status

# 添加本地目录到 knowledge base
kb add-local "/Users/zhiqli/Documents/project-notes"

# 添加网页到 knowledge base
kb add-url "https://docs.python.org/3/library/asyncio.html"

# 添加整个文档站点
kb add-site "https://fastapi.tiangolo.com" 50

# 搜索内容
kb search "asyncio event loop"

# 列出所有来源
kb list

# 添加 GitHub 仓库
kb add-repo "anthropics/anthropic-sdk-python"

# 删除来源
kb delete "web:docs.python.org/3/library/asyncio.html"
```

### 2. 使用 Python API

```python
import asyncio
from pathlib import Path
from kb.config import Config
from kb.core.storage import Storage
from kb.core.indexer import Indexer
from kb.core.retriever import Retriever
from kb.core.models import Source, SourceType, SourceStatus

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

### 3. MCP Server 集成

Knowledge Base 现在可以作为本地 MCP server 被 Claude Code 和 Cursor 直接使用。

#### Claude Code

项目级配置文件：`.mcp.json`

```json
{
  "mcpServers": {
    "knowledge-base": {
      "command": "python3",
      "args": ["-m", "kb.mcp.server"],
      "env": {
        "KNOWLEDGE_BASE_CONFIG": "~/.kb/config.json"
      }
    }
  }
}
```

#### Cursor

项目级配置文件：`.cursor/mcp.json`

```json
{
  "mcpServers": {
    "knowledge-base": {
      "command": "python3",
      "args": ["-m", "kb.mcp.server"],
      "env": {
        "KNOWLEDGE_BASE_CONFIG": "~/.kb/config.json"
      }
    }
  }
}
```

#### 可用 MCP tools

- `kb_add_local(path, include?, exclude?)`
- `kb_add_repo(repo_url, branch?, include?, exclude?)`
- `kb_add_url(url)`
- `kb_add_site(base_url, max_pages?)`
- `kb_search(query, n_results?, source_filter?)`
- `kb_list(source_type?)`
- `kb_status()`
- `kb_delete(source_id)`

#### 本地路径访问范围

为了避免 MCP 工具读取任意主机文件，`kb_add_local` 默认只允许索引当前工作目录下的内容。

如果你需要额外目录，请在 `~/.kb/config.json` 中配置：

```json
{
  "local": {
    "allowed_paths": [
      "/Users/zhiqli/Documents",
      "/Users/zhiqli/workspace"
    ],
    "allow_unrestricted_paths": false
  }
}
```

只有在明确知道风险时，才把 `allow_unrestricted_paths` 设为 `true`。

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
kb add-url "https://docs.python.org/3/library/asyncio.html"
kb search "asyncio library"
# ✅ 返回 3 个相关结果

# 测试 2: 查看状态
kb status
# ✅ 显示 1 个已索引来源

# 测试 3: 列出来源
kb list
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
   from kb.config import Config
   from kb.core.chroma_client import ChromaClient
   
   config = Config.load_default()
   chroma = ChromaClient(config.chroma)
   print(f"Chunks: {chroma.count()}")
   ```

3. 验证索引状态:
   ```bash
   kb status
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

1. **本地索引**: 当前以文本文件为主，未做 PDF/Office 原生解析
2. **GitHub 仓库索引**: 已实现，但仍建议继续补更多真实仓库测试
3. **网站 sitemap 索引**: 已实现，但对异常站点还可继续加强
4. **搜索分数**: 当前仍是纯向量分数，后续可考虑 hybrid retrieval / rerank

## 下一步

1. 增加本地目录增量重建 / file watching
2. 为 Cursor 和 Claude Code 增加更细的示例工作流
3. 测试 GitHub 仓库索引
4. 测试网站 sitemap 索引
5. 优化搜索相关性评分
