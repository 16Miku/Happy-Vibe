# Happy Vibe 开发规则

> 完整开发规则请参考 `.claude/CLAUDE.md`

## 快速参考

### 开发流程

```
开发模块 → 编写测试 → 运行测试 → 测试通过 → Git提交 → 更新进度
```

### 环境信息

- 操作系统: Windows
- Python 管理: uv
- 项目路径: `B:\study\AI\Happy-Vibe`
- Vibe-Kanban 项目ID: `3f101d13-0e36-4097-af11-e54734fc2694`

### 常用命令

```bash
# 运行测试
powershell -Command "cd 'B:\study\AI\Happy-Vibe\vibehub'; .\.venv\Scripts\activate; pytest tests/ -v"

# 安装依赖
powershell -Command "cd 'B:\study\AI\Happy-Vibe\vibehub'; uv pip install -e '.[dev]'"

# 代码检查
powershell -Command "cd 'B:\study\AI\Happy-Vibe\vibehub'; .\.venv\Scripts\activate; ruff check src/ --fix"
```

### 实时更新文件

| 文件 | 更新时机 |
|------|----------|
| `Note/开发指南.md` | 每次模块完成后更新进度 |
| `.gitignore` | 添加新的忽略项时 |
| `vibehub/pyproject.toml` | 添加新依赖时 |

### 提交信息格式

```
<类型>: <模块名> - <功能描述>

🤖 Generated with [Claude Code](https://claude.com/claude-code)
Co-Authored-By: Claude <noreply@anthropic.com>
```

类型: `feat:` | `fix:` | `test:` | `docs:` | `refactor:` | `perf:` | `style:` | `build:` | `chore:`
