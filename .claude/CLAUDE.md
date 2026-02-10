# Happy Vibe 开发规则

## 开发流程

本项目的开发遵循以下自动化流程：

```
开发模块 → 编写测试 → 运行测试 → 测试通过 → Git提交 → 更新进度
    ↑                                                      │
    └─────────── 测试失败 → 修复代码 ──────────────────────┘
```

---

## 一、Python 环境管理 (uv)

本项目使用 `uv` 作为 Python 包管理工具。

### 常用命令

```bash
# 创建虚拟环境
uv venv

# 激活虚拟环境
# Windows:
.venv\Scripts\activate
# Mac/Linux:
source .venv/bin/activate

# 安装依赖
uv pip install -r requirements.txt

# 安装单个包
uv pip install <package>

# 同步依赖（推荐）
uv pip sync requirements.txt

# 导出依赖
uv pip freeze > requirements.txt
```

### 项目初始化

```bash
cd vibehub
uv venv
.venv\Scripts\activate  # Windows
uv pip install -r requirements.txt
```

---

## 二、Vibe-Kanban 任务管理

本项目使用 `vibe-kanban-mcp` 进行任务管理和并行开发。

### 项目信息

- 项目名称: `Happy-Vibe`
- 项目ID: `3f101d13-0e36-4097-af11-e54734fc2694`

### 使用规则

1. **任务创建**: 开发新功能前，先在 vibe-kanban 创建对应任务
2. **状态更新**: 开始开发时更新任务状态为 `inprogress`
3. **完成标记**: 测试通过并提交后，更新任务状态为 `done`
4. **并行开发**: 独立模块可以创建多个任务并行开发

### 任务拆分原则

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

### MCP 工具调用示例

```
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

## 三、模块开发规范

- 每次只开发一个功能模块
- 模块完成后必须编写对应的单元测试
- 测试覆盖率要求：核心模块 ≥ 80%，其他模块 ≥ 60%
- 代码必须包含类型注解和文档字符串

---

## 四、自动化测试规范

### Python 项目 (vibehub/)

```bash
# 进入项目目录
cd vibehub

# 激活环境
.venv\Scripts\activate

# 运行测试
pytest tests/ -v --cov=src --cov-report=term-missing

# 测试通过标准
# - 所有测试用例通过
# - 覆盖率达到要求
# - 无 mypy 类型错误
# - 无 ruff/lint 错误
```

### Godot 项目 (game/)

```bash
# 运行 Godot 单元测试（使用 GUT 框架）
# godot --headless --script addons/gut/gut_cmdline.gd -res://tests/tests.gd
```

---

## 五、Git 提交规范

### 提交前检查

1. 运行测试确保通过
2. 生成中文提交信息
3. 更新开发进度文档

### 提交信息格式

```bash
git commit -m "<类型>: <模块名> - <功能描述>

详细内容：
- 实现功能: ...
- 测试覆盖: ...

🤖 Generated with [Claude Code](https://claude.com/claude-code)

Co-Authored-By: Claude <noreply@anthropic.com>"
```

### 提交信息类型

| 类型 | 前缀 | 示例 |
|------|------|------|
| 新功能 | `feat:` | `feat: 能量计算模块 - 实现基础能量计算算法` |
| 修复 | `fix:` | `fix: 数据采集器 - 修复日志解析边界问题` |
| 测试 | `test:` | `test: 能量计算器 - 添加质量评分测试用例` |
| 文档 | `docs:` | `docs: API文档 - 更新能量计算端点说明` |
| 重构 | `refactor:` | `refactor: 适配器基类 - 提取公共接口` |
| 性能 | `perf:` | `perf: 日志监听 - 使用异步IO提升性能` |
| 样式 | `style:` | `style: 代码格式化 - 统一使用 ruff 格式化` |

---

## 六、开发进度更新

每次完成模块开发并提交后，必须更新 `Note/开发指南.md` 中的开发检查清单。

### 更新位置

文件: `Note/开发指南.md`
章节: `七、开发检查清单`

### 更新格式

```markdown
- [x] 已完成的任务
- [ ] 待完成的任务
```

---

## 七、分支策略

```
main (主分支，稳定版本)
  ├── dev (开发分支，集成测试通过)
  │     ├── feature/<module-name> (功能分支)
  │     └── fix/<bug-name> (修复分支)
  └── release/<version> (发布分支)
```

---

## 八、代码质量标准

### Python 代码

```bash
# 类型检查
mypy src/

# 代码格式化
ruff format src/

# 代码检查
ruff check src/ --fix
```

### GDScript 代码

- 类命名：PascalCase
- 函数命名：snake_case
- 常量：UPPER_CASE
- 私有变量：_前缀

---

## 九、测试命名规范

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

## 十、执行命令

开始开发新模块时，请声明：

```
开始开发 <模块名>
- 目标: <功能描述>
- 依赖: <前置模块>
- 测试计划: <测试内容>
```

完成模块时，请执行：

1. 运行测试验证
2. 确认测试通过
3. 自动提交代码（中文提交信息）
4. 更新 vibe-kanban 任务状态
5. 更新开发指南进度
