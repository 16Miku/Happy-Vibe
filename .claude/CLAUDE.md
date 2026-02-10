# Happy Vibe 开发规则

## 开发流程

本项目的开发遵循以下自动化流程：

```
开发模块 → 编写测试 → 运行测试 → 测试通过 → Git提交 → 更新进度
    ↑                                                      │
    └─────────── 测试失败 → 修复代码 ──────────────────────┘
```

---

## 一、开发环境说明

### 1.1 系统环境

- 操作系统: Windows
- Shell: PowerShell (使用 `powershell -Command "..."` 执行命令)
- 项目路径: `B:\study\AI\Happy-Vibe`

### 1.2 命令执行规范

由于本项目在 Windows 环境下开发，所有 Bash 命令需要通过 PowerShell 执行：

```bash
# 正确的命令执行方式
powershell -Command "cd 'B:\study\AI\Happy-Vibe\vibehub'; <命令>"

# 示例：运行测试
powershell -Command "cd 'B:\study\AI\Happy-Vibe\vibehub'; .\.venv\Scripts\activate; pytest tests/ -v"

# 示例：安装依赖
powershell -Command "cd 'B:\study\AI\Happy-Vibe\vibehub'; uv pip install -e '.[dev]'"
```

### 1.3 路径规范

- 使用单引号包裹包含空格或特殊字符的路径
- Windows 路径使用反斜杠 `\` 或正斜杠 `/`
- 项目根目录: `B:\study\AI\Happy-Vibe`

---

## 二、Python 环境管理 (uv)

本项目使用 `uv` 作为 Python 包管理工具。

### 2.1 环境信息

- Python 版本: 3.14.3
- 虚拟环境路径: `vibehub/.venv`
- 依赖配置: `vibehub/pyproject.toml`

### 2.2 常用命令

```bash
# 创建虚拟环境
powershell -Command "cd 'B:\study\AI\Happy-Vibe\vibehub'; uv venv"

# 安装所有依赖（包括开发依赖）
powershell -Command "cd 'B:\study\AI\Happy-Vibe\vibehub'; uv pip install -e '.[dev]'"

# 安装单个包
powershell -Command "cd 'B:\study\AI\Happy-Vibe\vibehub'; uv pip install <package>"

# 更新依赖
powershell -Command "cd 'B:\study\AI\Happy-Vibe\vibehub'; uv pip install -e '.[dev]' --upgrade"
```

### 2.3 新会话初始化

每次新会话开始时，如果需要运行 Python 相关命令，确保：

1. 虚拟环境已存在 (`vibehub/.venv`)
2. 依赖已安装
3. 使用正确的 PowerShell 命令格式

---

## 三、Vibe-Kanban 任务管理

本项目使用 `vibe-kanban-mcp` 进行任务管理和并行开发。

### 3.1 项目信息

- 项目名称: `Happy-Vibe`
- 项目ID: `3f101d13-0e36-4097-af11-e54734fc2694`

### 3.2 使用规则

1. **任务创建**: 开发新功能前，先在 vibe-kanban 创建对应任务
2. **状态更新**: 开始开发时更新任务状态为 `inprogress`
3. **完成标记**: 测试通过并提交后，更新任务状态为 `done`
4. **并行开发**: 独立模块可以创建多个任务并行开发

### 3.3 任务拆分原则

```
可并行任务（无依赖）:
├── 能量计算核心模块
├── Claude Code 日志适配器
├── 数据库模型设计
├── Godot 游戏框架
└── UI 界面系统

需串行任务（有依赖）:
├── REST API 端点 → 依赖核心模块
├── 网络通信模块 → 依赖 API 端点
└── 桌面监控器 → 依赖 API 端点
```

### 3.4 MCP 工具调用示例

```python
# 列出任务
mcp__vibe_kanban__list_tasks(project_id="3f101d13-0e36-4097-af11-e54734fc2694")

# 创建任务
mcp__vibe_kanban__create_task(
    project_id="3f101d13-0e36-4097-af11-e54734fc2694",
    title="实现能量计算核心模块",
    description="实现基于编码时长、质量、心流状态的能量计算算法"
)

# 更新任务状态
mcp__vibe_kanban__update_task(task_id="<task_id>", status="inprogress")
mcp__vibe_kanban__update_task(task_id="<task_id>", status="done")
```

---

## 四、实时更新文件清单

以下文件需要在开发过程中实时更新，确保项目状态同步：

### 4.1 必须更新的文件

| 文件 | 更新时机 | 更新内容 |
|------|----------|----------|
| `Note/开发指南.md` | 每次模块完成后 | 更新「七、开发检查清单」中的进度 |
| `.gitignore` | 添加新的构建产物/缓存时 | 添加需要忽略的文件模式 |
| `vibehub/pyproject.toml` | 添加新依赖时 | 更新 dependencies 列表 |
| `CLAUDE.md` | 开发规则变更时 | 更新开发规范和流程 |

### 4.2 .gitignore 维护规则

当出现以下情况时，必须更新 `.gitignore`：

```gitignore
# Python 相关
__pycache__/
*.py[cod]
*$py.class
*.so
.Python
.venv/
venv/
*.egg-info/
dist/
build/

# 测试和覆盖率
.pytest_cache/
.coverage
htmlcov/
.tox/
.nox/

# IDE 和编辑器
.idea/
.vscode/
*.swp
*.swo
*~

# Godot 相关
.godot/
*.import
export_presets.cfg

# 系统文件
.DS_Store
Thumbs.db

# 日志和临时文件
*.log
*.tmp
```

### 4.3 开发进度更新规范

每次完成模块开发并提交后，必须更新 `Note/开发指南.md`：

**更新位置**: 章节「七、开发检查清单」

**更新格式**:
```markdown
- [x] 已完成的任务 (附加说明，如测试覆盖率)
- [ ] 待完成的任务
```

**示例**:
```markdown
### Phase 1 - 技术验证
- [x] VibeHub服务框架完成 (FastAPI + 健康检查API, 测试覆盖87%)
- [ ] Claude Code日志解析实现
```

---

## 五、模块开发规范

### 5.1 基本原则

- 每次只开发一个功能模块
- 模块完成后必须编写对应的单元测试
- 测试覆盖率要求：核心模块 ≥ 80%，其他模块 ≥ 60%
- 代码必须包含类型注解和文档字符串

### 5.2 模块开发声明

开始开发新模块时，请声明：

```
开始开发 <模块名>
- 目标: <功能描述>
- 依赖: <前置模块>
- 测试计划: <测试内容>
```

### 5.3 模块完成检查

完成模块时，请执行：

1. 运行测试验证
2. 确认测试通过
3. 自动提交代码（中文提交信息）
4. 更新 vibe-kanban 任务状态
5. 更新 `Note/开发指南.md` 进度

---

## 六、自动化测试规范

### 6.1 Python 项目 (vibehub/)

```bash
# 运行测试
powershell -Command "cd 'B:\study\AI\Happy-Vibe\vibehub'; .\.venv\Scripts\activate; pytest tests/ -v --cov=src --cov-report=term-missing"

# 测试通过标准
# - 所有测试用例通过
# - 覆盖率达到要求
# - 无 mypy 类型错误
# - 无 ruff/lint 错误
```

### 6.2 代码质量检查

```bash
# 类型检查
powershell -Command "cd 'B:\study\AI\Happy-Vibe\vibehub'; .\.venv\Scripts\activate; mypy src/"

# 代码格式化
powershell -Command "cd 'B:\study\AI\Happy-Vibe\vibehub'; .\.venv\Scripts\activate; ruff format src/"

# 代码检查
powershell -Command "cd 'B:\study\AI\Happy-Vibe\vibehub'; .\.venv\Scripts\activate; ruff check src/ --fix"
```

### 6.3 Godot 项目 (game/)

```bash
# 运行 Godot 单元测试（使用 GUT 框架）
# godot --headless --script addons/gut/gut_cmdline.gd -res://tests/tests.gd
```

### 6.4 测试命名规范

```python
# 测试文件命名: test_<module_name>.py
# 测试类命名: Test<ClassName>
# 测试函数命名: test_<function_name>_<scenario>

class TestEnergyCalculator:
    def test_calculate_base_energy(self):
        """测试基础能量计算"""
        pass

    def test_calculate_with_flow_state(self):
        """测试心流状态加成"""
        pass

    def test_calculate_zero_duration_returns_zero(self):
        """测试零时长返回零能量"""
        pass
```

---

## 七、Git 提交规范

### 7.1 提交前检查清单

1. [ ] 运行测试确保通过
2. [ ] 代码格式化 (ruff format)
3. [ ] 代码检查 (ruff check)
4. [ ] 更新 .gitignore（如有新的忽略项）
5. [ ] 生成中文提交信息
6. [ ] 更新开发进度文档

### 7.2 提交信息格式

```bash
git commit -m "$(cat <<'EOF'
<类型>: <模块名> - <功能描述>

详细内容：
- 实现功能: ...
- 测试覆盖: ...

🤖 Generated with [Claude Code](https://claude.com/claude-code)

Co-Authored-By: Claude <noreply@anthropic.com>
EOF
)"
```

### 7.3 提交信息类型

| 类型 | 前缀 | 示例 |
|------|------|------|
| 新功能 | `feat:` | `feat: 能量计算模块 - 实现基础能量计算算法` |
| 修复 | `fix:` | `fix: 数据采集器 - 修复日志解析边界问题` |
| 测试 | `test:` | `test: 能量计算器 - 添加质量评分测试用例` |
| 文档 | `docs:` | `docs: API文档 - 更新能量计算端点说明` |
| 重构 | `refactor:` | `refactor: 适配器基类 - 提取公共接口` |
| 性能 | `perf:` | `perf: 日志监听 - 使用异步IO提升性能` |
| 样式 | `style:` | `style: 代码格式化 - 统一使用 ruff 格式化` |
| 构建 | `build:` | `build: 依赖更新 - 升级 FastAPI 版本` |
| 杂项 | `chore:` | `chore: 配置更新 - 添加 .gitignore 规则` |

---

## 八、分支策略

```
main (主分支，稳定版本)
  ├── dev (开发分支，集成测试通过)
  │     ├── feature/<module-name> (功能分支)
  │     └── fix/<bug-name> (修复分支)
  └── release/<version> (发布分支)
```

---

## 九、代码质量标准

### 9.1 Python 代码规范

- 使用类型注解
- 编写文档字符串 (Google 风格)
- 遵循 PEP 8 规范
- 使用 ruff 进行格式化和检查

### 9.2 GDScript 代码规范

- 类命名：PascalCase
- 函数命名：snake_case
- 常量：UPPER_CASE
- 私有变量：_前缀
- 信号命名：snake_case

### 9.3 文档规范

- 所有公共函数必须有文档字符串
- 复杂逻辑需要添加注释
- API 端点需要添加 OpenAPI 描述

---

## 十、项目结构

```
B:\study\AI\Happy-Vibe\
├── .claude/                    # Claude Code 配置
│   └── CLAUDE.md               # 开发规则（本文件）
├── Note/                       # 项目文档
│   ├── Spec-Driven-Development.md  # 完整设计文档
│   └── 开发指南.md              # 开发指南和进度
├── vibehub/                    # VibeHub 本地服务
│   ├── .venv/                  # Python 虚拟环境
│   ├── src/                    # 源代码
│   │   ├── api/                # API 路由
│   │   ├── config/             # 配置
│   │   ├── core/               # 核心逻辑（待开发）
│   │   ├── adapters/           # 数据适配器（待开发）
│   │   └── storage/            # 存储层（待开发）
│   ├── tests/                  # 测试文件
│   ├── pyproject.toml          # 项目配置
│   └── requirements.txt        # 依赖列表
├── game/                       # Godot 游戏客户端（待开发）
├── monitor/                    # 桌面监控器（待开发）
├── .gitignore                  # Git 忽略规则
└── CLAUDE.md                   # 根目录开发规则副本
```

---

## 十一、常见问题排查

### 11.1 命令执行失败

如果命令执行失败，检查：
1. 是否使用了正确的 PowerShell 格式
2. 路径是否正确（使用单引号包裹）
3. 虚拟环境是否已创建

### 11.2 依赖安装失败

如果依赖安装失败（网络问题）：
1. 检查代理设置（Clash 等）
2. 使用 `uv pip install` 重试
3. 考虑使用国内镜像源

### 11.3 测试失败

如果测试失败：
1. 查看具体错误信息
2. 检查是否有未安装的依赖
3. 确认代码逻辑是否正确
4. 修复后重新运行测试

---

## 十二、安全规范

### 12.1 敏感信息处理

- 不要将 API 密钥、密码等敏感信息提交到 Git
- 使用环境变量或 `.env` 文件管理敏感配置
- `.env` 文件必须添加到 `.gitignore`

### 12.2 代码安全

- 避免 SQL 注入、XSS 等常见漏洞
- 对用户输入进行验证和清理
- 使用参数化查询操作数据库
