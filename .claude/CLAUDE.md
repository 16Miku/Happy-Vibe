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

## 三、Vibe-Kanban 并行开发模式

本项目使用 `vibe-kanban-mcp` 进行任务管理和并行开发。

### 3.1 概述

vibe-kanban MCP 是一个任务管理系统，支持启动独立的 Claude Code agent 会话进行并行开发。每个任务在独立工作区执行，完成后自动合并到主分支。适用于多个**完全独立、无依赖**的任务同时开发。

### 3.2 项目和仓库信息

| 项目 | ID |
|------|-----|
| 项目名称 | `Happy-Vibe` |
| 项目ID | `3f101d13-0e36-4097-af11-e54734fc2694` |
| 仓库ID | `e38a6122-023a-4e30-bbf5-b9499c2d3a8c` |
| 基础分支 | `main` |

### 3.3 使用场景

**适合 vibe-kanban 并行的任务：**
- 独立的功能模块开发（如能量计算、日志适配器、数据库模型）
- 独立的 UI 组件开发
- E2E 测试编写
- API 文档完善
- Godot 游戏场景开发

**不适合 vibe-kanban 的任务：**
- 有依赖关系的功能（如 REST API 依赖核心模块）
- 需要实时调试的核心功能
- 前后端联调
- Bug 修复
- 需要频繁交互确认的任务

### 3.4 操作流程

```
1. 创建任务 (MCP) → 2. 启动 workspace → 3. 独立 agent 执行 → 4. 自动合并到主分支 → 5. 代码审查
```

**工作原理**:
- 每个任务启动一个独立的 Claude Code agent 会话
- 在独立工作区内执行开发
- 完成后自动合并代码到主分支
- 本地执行，非云端

### 3.5 任务描述规范

**重要**: 独立工作区是隔离的，任务描述必须包含完整上下文！

任务描述模板：
```markdown
## 目标
<清晰描述要实现的功能>

## 背景
<相关的项目背景和上下文>

## 实现步骤
1. <步骤1>
2. <步骤2>
3. ...

## 技术要求
- <技术规范1>
- <技术规范2>

## 文件位置
- 源代码: `vibehub/src/<module>/`
- 测试文件: `vibehub/tests/test_<module>.py`

## 验收标准
- [ ] 功能实现完成
- [ ] 单元测试通过，覆盖率 ≥ 80%
- [ ] 代码通过 ruff check 和 mypy 检查
- [ ] 中文 Git 提交信息
```

### 3.6 MCP 服务可用性检查

⚠️ **重要提示**：每次使用 vibe-kanban MCP 工具前，务必检查服务可用性和工具更新！

```python
# 步骤 1：检查服务是否可用（每次使用前必做）
try:
    # 调用简单方法验证服务连接
    orgs = mcp__vibe_kanban__list_organizations()
    print("✓ vibe-kanban 服务可用")
except Exception as e:
    print(f"❌ vibe-kanban 服务不可用: {e}")
    print("请使用 /mcp 命令重新连接 vibe-kanban")
    # 不要继续执行后续操作
    exit()

# 步骤 2：验证所需工具是否存在
# 可用工具列表可能随时更新，使用前务必确认
required_tools = [
    "mcp__vibe_kanban__list_organizations",
    "mcp__vibe_kanban__list_projects",
    "mcp__vibe_kanban__list_issues",
    "mcp__vibe_kanban__create_issue",
    "mcp__vibe_kanban__start_workspace_session",  # 注意：必须带 issue_id 参数
    "mcp__vibe_kanban__get_issue",
    "mcp__vibe_kanban__update_issue",
]
```

**常见问题排查**：
- **502 Bad Gateway**: 服务暂时不可用，请稍后重试或重新连接
- **工具名称不存在**: MCP 服务可能更新了工具名称，请重新检查可用工具
- **任务状态未更新**: 检查 `start_workspace_session` 是否包含了 `issue_id` 参数

### 3.7 MCP 工具调用示例

```python
# 1. 列出组织
mcp__vibe_kanban__list_organizations()

# 2. 列出项目
mcp__vibe_kanban__list_projects(organization_id="06b32dcb-1bf1-41f9-934e-6b1b1b9f8360")

# 3. 创建任务（包含详细描述）
mcp__vibe_kanban__create_issue(
    project_id="2b422040-034e-444d-a7bb-9243c049b494",
    title="实现能量计算核心模块",
    description="""
## 目标
实现基于编码时长、质量、心流状态的 Vibe 能量计算算法。

## 背景
Happy Vibe 游戏的核心机制是将真实的 Vibe-Coding 活动转化为游戏内能量。
能量计算需要考虑：编码时长、代码质量、心流状态等因素。

## 实现步骤
1. 创建 `vibehub/src/core/` 目录
2. 实现 `energy_calculator.py` 能量计算器类
3. 实现 `flow_detector.py` 心流状态检测
4. 实现 `quality_scorer.py` 质量评分器
5. 编写完整的单元测试

## 技术要求
- 使用 Python 类型注解
- 编写 Google 风格文档字符串
- 遵循项目代码规范 (ruff)

## 文件位置
- 源代码: `vibehub/src/core/`
- 测试文件: `vibehub/tests/test_energy_calculator.py`

## 验收标准
- [ ] EnergyCalculator 类实现完成
- [ ] 支持基础能量、时间加成、质量加成、心流加成计算
- [ ] 单元测试覆盖率 ≥ 80%
- [ ] 代码通过 ruff check 和 mypy 检查
"""
)

# 4. 列出仓库（获取 repo_id）
mcp__vibe_kanban__list_repos()

# 5. 配置 setup script（云端环境初始化）
mcp__vibe_kanban__update_setup_script(
    repo_id="e38a6122-023a-4e30-bbf5-b9499c2d3a8c",
    script="cd vibehub && uv venv && uv pip install -e '.[dev]'"
)

# 6. 启动工作空间（包含 issue_id 参数，重要！）
mcp__vibe_kanban__start_workspace_session(
    issue_id="<issue_id>",  # ← 关键参数！必须包含 issue_id
    title="任务标题",
    executor="CLAUDE_CODE",
    repos=[{"repo_id": "e38a6122-023a-4e30-bbf5-b9499c2d3a8c", "base_branch": "main"}]
)

# 7. 列出任务
mcp__vibe_kanban__list_issues(project_id="2b422040-034e-444d-a7bb-9243c049b494")

# 8. 获取任务详情
mcp__vibe_kanban__get_issue(issue_id="<issue_id>")

# 9. 更新任务状态
mcp__vibe_kanban__update_issue(issue_id="<issue_id>", status="done")

# 10. 链接工作空间到任务（可选）
mcp__vibe_kanban__link_workspace(
    workspace_id="<workspace_id>",
    issue_id="<issue_id>"
)
```

### 3.8 注意事项

1. **不要重复创建任务**: vibe-kanban 云端任务和本地开发是不同的，不要同时进行
2. **任务描述要详细**: 云端工作空间是独立的，需要完整的上下文
3. **配置 setup script**: 云端需要知道如何安装依赖
4. **合并后审查**: 任务完成合并到 main 后，必须进行代码审查
5. **避免冲突**: 并行任务应该修改不同的文件，避免合并冲突

### 3.9 任务拆分原则

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
