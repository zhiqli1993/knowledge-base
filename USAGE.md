# Knowledge Base 使用指南

## 1. 总体说明

当前系统的工作方式是：

- `kb` CLI 不再直接操作 SQLite / Chroma
- `kb.mcp.server` 也不再直接操作索引层
- CLI 和 MCP 都通过 HTTP 访问同一个 KB Web Service
- 本地服务由 `kb serve/stop/restart` 管理

这让 CLI、MCP、后台索引、状态、进度都共享同一套行为。

## 2. 快速开始

### 安装

```bash
pip install -e .
```

### 准备配置

默认配置文件：

```bash
~/.kb/config.json
```

最小可用示例：

```json
{
  "ollama": {
    "host": "localhost",
    "port": 11434,
    "model": "nomic-embed-text",
    "timeout": 60
  },
  "service": {
    "host": "127.0.0.1",
    "port": 8864,
    "timeout_seconds": 30
  },
  "local": {
    "allowed_paths": [
      "/Users/your-user/Documents"
    ],
    "allow_unrestricted_paths": false
  }
}
```

### 启动本地服务

```bash
kb serve
```

### 查看状态

```bash
kb status
```

## 3. CLI 命令

### 服务生命周期

```bash
kb serve
kb stop
kb restart
kb logs
kb logs 100
```

### 连接本地或远程服务

```bash
kb connect http://10.0.0.8:8864
kb connect local
```

说明：

- `kb connect <url>` 会把 CLI 指向远程 KB 服务
- `kb connect local` 会回到本地 `service.host/service.port`
- 配置会写回 `~/.kb/config.json`

### 添加内容

```bash
kb add-local "/Users/your-user/Documents/project-notes"
kb add-url "https://docs.python.org/3/library/asyncio.html"
kb add-site "https://fastapi.tiangolo.com" 50
kb add-repo "anthropics/anthropic-sdk-python"
```

说明：

- 如果不传 `branch`，系统会自动探测远端仓库默认分支
- 这同样适用于企业 GitHub / GitHub Enterprise 风格的 HTTPS 仓库 URL

### 查询与管理

```bash
kb list
kb list local
kb progress "local:/absolute/path/to/file.md"
kb search "asyncio event loop"
kb delete "web:docs.python.org/3/library/asyncio.html"
kb update --all
kb update "github:owner/repo"
kb reindex --all
kb reindex "local:/absolute/path/to/notes"
```

## 4. 进度查看

索引进度已经持久化到元数据中，CLI 和 MCP 都可以看到同一份进度信息。

### CLI 查看

```bash
kb progress "local:/absolute/path/to/file.md"
```

### 返回内容包含

- source id
- status
- document_count
- chunk_count
- progress_total
- progress_processed
- progress_phase
- progress_message

## 5. MCP Server 集成

Knowledge Base 可以作为本地 MCP server 被 Claude Code 和 Cursor 直接使用。

### Claude Code

项目级配置文件：`.mcp.json`

```json
{
  "mcpServers": {
    "knowledge-base": {
      "command": "python3",
      "args": ["-m", "kb.mcp.server"],
      "env": {
        "KNOWLEDGE_BASE_CONFIG": "/Users/your-user/.kb/config.json"
      }
    }
  }
}
```

### Cursor

项目级配置文件：`.cursor/mcp.json`

```json
{
  "mcpServers": {
    "knowledge-base": {
      "command": "python3",
      "args": ["-m", "kb.mcp.server"],
      "env": {
        "KNOWLEDGE_BASE_CONFIG": "/Users/your-user/.kb/config.json"
      }
    }
  }
}
```

### 可用 MCP tools

- `kb_add_local(path, include?, exclude?)`
- `kb_add_repo(repo_url, branch?, include?, exclude?)`
- `kb_add_url(url)`
- `kb_add_site(base_url, max_pages?)`
- `kb_search(query, n_results?, source_filter?)`
- `kb_list(source_type?)`
- `kb_status()`
- `kb_progress(source_id)`
- `kb_update(source_id?)`
- `kb_reindex(source_id?)`
- `kb_delete(source_id)`

## 6. 本地路径访问范围

为了避免 AI 代理读取任意主机文件，`kb_add_local` 仍然受 allowlist 保护。

配置位置：

```bash
~/.kb/config.json
```

示例：

```json
{
  "local": {
    "allowed_paths": [
      "/Users/your-user/Documents",
      "/Users/your-user/workspace"
    ],
    "allow_unrestricted_paths": false
  }
}
```

## 7. 远程服务注意事项

如果 CLI 或 MCP 指向远程 KB 服务：

- `add-local` 的路径是**远程服务主机上的路径**，不是当前本机路径
- `serve/stop/restart/logs` 只管理本地服务
- `connect` 只影响客户端指向，不会自动启动远程服务

## 8. Python API

如果你需要直接在 Python 中嵌入核心组件，可以使用：

```python
import asyncio
from kb.config import Config
from kb.core.storage import Storage
from kb.core.indexer import Indexer
from kb.core.retriever import Retriever

async def main():
    config = Config.load_default()
    storage = Storage(config.chroma.persist_directory_expanded / "storage.db")
    await storage.init()

    indexer = Indexer(config)
    await indexer.initialize()

    retriever = Retriever(config)
    results = await retriever.search("asyncio", n_results=5)
    print(results)

asyncio.run(main())
```

注意：当前推荐的人机使用路径仍然是 `kb` CLI 或 MCP + Web Service。

## 9. 故障排查

### `kb status` 无法连接

先确认服务是否启动：

```bash
kb serve
kb status
```

### `kb logs` 为空

这是正常的。当前服务默认只有少量启动日志；如果没有异常，日志可能为空。

### 搜索无结果

1. 检查 Ollama：

```bash
curl http://localhost:11434/api/tags
```

2. 检查 source 状态和进度：

```bash
kb list
kb progress <source-id>
```

3. 尝试更语义化的查询，而不是只搜单个关键词。

## 10. 当前已验证能力

- 本地服务生命周期命令
- 远程连接切换
- 进度显示
- 本地文件索引
- MCP 代理到 Web Service
- CLI 代理到 Web Service
- 全量测试通过
