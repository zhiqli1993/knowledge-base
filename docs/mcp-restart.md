# MCP Reload / Restart Notes

现在的 MCP server (`kb.mcp.server`) 是 **KB Web Service 的代理层**。

这意味着：

- MCP 自己不直接持有索引状态
- 真正的索引、搜索、删除、进度都在 Web Service 里
- 如果 MCP 失效，通常需要检查的是“服务是否可用”与“客户端配置是否正确”

## 推荐排查顺序

### 1. 先确认本地服务正常

```bash
kb serve
kb status
```

### 2. 检查 MCP 配置

`.mcp.json` 示例：

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

## 如果 MCP 看起来没更新

### Claude Code

1. 完全退出 Claude Code
2. 重新启动 Claude Code
3. 再测试 MCP 工具

### Cursor

1. 重新加载 MCP 配置
2. 如有必要，重启 Cursor

## 推荐验证命令

重载后优先验证：

- `kb_status`
- `kb_list`
- `kb_progress`
- `kb_search`

## 临时替代方案

在 MCP 没恢复前，可以直接用 CLI：

```bash
kb status
kb list
kb search "your query"
kb add-url https://example.com
kb add-repo owner/repo
```
