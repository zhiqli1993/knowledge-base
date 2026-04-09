# Knowledge Base Testing Guide

## 当前测试策略

项目已经从“CLI / MCP 直连核心存储”切换为“CLI / MCP → Web Service → core”。

因此测试需要覆盖三层：

1. `core` 单元测试
2. `MCP proxy` 集成测试
3. `CLI + Web Service` 端到端验证

## 1. 快速回归

```bash
cd /Users/zhiqli/knowledge-base
pytest -q
```

当前最新结果：

```text
77 passed
```

## 2. 重点测试命令

### 核心单测

```bash
pytest tests/unit/test_config.py -q
pytest tests/unit/test_storage.py -q
pytest tests/unit/test_indexer.py -q
```

### MCP 集成测试

```bash
pytest tests/integration/test_mcp_server.py -q
```

### 结构测试

```bash
pytest tests/test_project_structure.py -q
```

## 3. 手工验证本地服务

### 启动

```bash
kb serve
```

### 查看状态

```bash
kb status
```

### 添加本地文件

```bash
kb add-local "/absolute/path/to/file.md"
```

### 查看进度

```bash
kb progress "local:/absolute/path/to/file.md"
```

### 搜索

```bash
kb search "your semantic query"
```

### 查看日志

```bash
kb logs
```

### 停止

```bash
kb stop
```

## 4. 手工验证远程连接

```bash
kb connect http://127.0.0.1:8864
kb status
kb connect local
```

## 5. 手工验证 MCP 代理

前提：

- `pip install -e .`
- `kb serve`
- `.mcp.json` / `.cursor/mcp.json` 指向 `python3 -m kb.mcp.server`

测试点：

- `kb_status`
- `kb_add_local`
- `kb_progress`
- `kb_search`
- `kb_delete`

## 6. 当前真实验证结论

已经验证：

- CLI 通过 Web Service 完整执行 `serve/status/add-local/progress/search/connect/logs/delete/stop`
- MCP 通过 Web Service 完整执行 `kb_add_local/kb_progress/kb_search/kb_status/kb_delete`
- 全量 pytest 通过

## 7. 常见问题

### 连接被拒绝

说明本地服务没起来，先运行：

```bash
kb serve
```

### Ollama 未启动

```bash
ollama serve
```

### 搜索无结果

优先看：

```bash
kb progress <source-id>
```

如果 source 还没 `ready`，等待索引完成后再搜。
