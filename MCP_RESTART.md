# MCP Server 重启指南

## 问题
MCP 工具（kb_status, kb_list, kb_search）卡住或返回错误。

## 原因
MCP server 进程在运行旧代码，需要重新加载最新的修复。

## 解决方案

### 方法 1: 重启 Claude Code（推荐）
1. 完全退出 Claude Code
2. 重新启动 Claude Code
3. MCP server 会自动加载最新代码

### 方法 2: 手动重启 MCP server（如果支持）
如果 Claude Code 支持重启单个 MCP server：
1. 使用 Claude Code 的 MCP 管理界面
2. 重启 `knowledge-base` server

### 方法 3: 验证配置
确保 `.mcp.json` 配置正确：

```json
{
  "mcpServers": {
    "knowledge-base": {
      "command": "python3",
      "args": ["-m", "mcp_server.server"],
      "env": {
        "KNOWLEDGE_BASE_CONFIG": "/Users/zhiqli/.config/knowledge-base/config.json",
        "PYTHONPATH": "/Users/zhiqli/knowledge-base"
      }
    }
  }
}
```

## 验证修复

重启后测试以下 MCP 工具：

```
kb_status -> 应该返回知识库统计信息
kb_list -> 应该列出 3 个源
kb_search "FastAPI" -> 应该返回搜索结果
```

## 预期结果

```
Knowledge Base Status:

Sources:
  Total: 3
  Indexed: 3
  Indexing: 0
  Pending: 0
  Failed: 0

Documents: 3
Chunks: [数量]

Storage: /Users/zhiqli/.local/share/knowledge-base/chroma
Embedding Model: nomic-embed-text
```

## 临时解决方案

在 MCP server 重启之前，可以使用 Python CLI:

```bash
# 检查状态
python3 kb_cli.py status

# 搜索
python3 kb_cli.py search "your query"

# 添加源
python3 kb_cli.py add-url https://example.com
python3 kb_cli.py add-repo owner/repo
```

所有功能都可以通过 CLI 正常使用！
