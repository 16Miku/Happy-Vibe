# Happy Vibe 开发规则

## 开发流程

本项目的开发遵循以下自动化流程：

```
开发模块 → 编写测试 → 运行测试 → 测试通过 → Git提交
    ↑                                           │
    └─────────── 测试失败 → 修复代码 ───────────┘
```

## 详细规则

### 1. 模块开发规范

- 每次只开发一个功能模块
- 模块完成后必须编写对应的单元测试
- 测试覆盖率要求：核心模块 ≥ 80%，其他模块 ≥ 60%
- 代码必须包含类型注解和文档字符串

### 2. 自动化测试规范

#### Python 项目 (vibehub/)

```bash
# 测试命令
cd vibehub
pytest tests/ -v --cov=src --cov-report=term-missing

# 测试通过标准
# - 所有测试用例通过
# - 覆盖率达到要求
# - 无 mypy 类型错误
# - 无 ruff/lint 错误
```

#### Godot 项目 (game/)

```bash
# 运行 Godot 单元测试（使用 GUT 框架）
# godot --headless --script addons/gut/gut_cmdline.gd -res://tests/tests.gd
```

### 3. 自动化提交规范

测试通过后，自动执行 Git 提交：

```bash
# 1. 添加更改的文件
git add <module_files>

# 2. 生成中文提交信息并提交
git commit -m "<中文提交信息>

# 提交信息格式：
# feat: <模块名> - <功能描述>
#
# 详细内容：
# - 实现功能: ...
# - 测试覆盖: ...
#
# 🤖 Generated with [Claude Code](https://claude.com/claude-code)
#
# Co-Authored-By: Claude <noreply@anthropic.com>
```

### 4. 提交信息类型

| 类型 | 前缀 | 示例 |
|------|------|------|
| 新功能 | `feat:` | `feat: 能量计算模块 - 实现基础能量计算算法` |
| 修复 | `fix:` | `fix: 数据采集器 - 修复日志解析边界问题` |
| 测试 | `test:` | `test: 能量计算器 - 添加质量评分测试用例` |
| 文档 | `docs:` | `docs: API文档 - 更新能量计算端点说明` |
| 重构 | `refactor:` | `refactor: 适配器基类 - 提取公共接口` |
| 性能 | `perf:` | `perf: 日志监听 - 使用异步IO提升性能` |
| 样式 | `style:` | `style: 代码格式化 - 统一使用 ruff 格式化` |

### 5. 分支策略

```
main (主分支，稳定版本)
  ├── dev (开发分支，集成测试通过)
  │     ├── feature/<module-name> (功能分支)
  │     └── fix/<bug-name> (修复分支)
  └── release/<version> (发布分支)
```

### 6. 代码质量标准

#### Python 代码

```bash
# 类型检查
mypy src/

# 代码格式化
ruff format src/

# 代码检查
ruff check src/ --fix
```

#### GDScript 代码

- 使用类命名规范：PascalCase
- 使用函数命名规范：snake_case
- 常量使用 UPPER_CASE
- 私有变量使用 _前缀

### 7. 测试命名规范

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

## 执行命令

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
3. 自动提交代码
