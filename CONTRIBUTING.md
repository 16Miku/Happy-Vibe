# 贡献指南

感谢你对 Happy Vibe 项目的关注！我们欢迎各种形式的贡献。

## 目录

- [行为准则](#行为准则)
- [如何贡献](#如何贡献)
- [开发流程](#开发流程)
- [提交规范](#提交规范)
- [代码审查](#代码审查)

---

## 行为准则

- 尊重所有贡献者
- 保持友善和建设性的讨论
- 专注于技术问题本身

---

## 如何贡献

### 报告 Bug

1. 在 [Issues](https://github.com/your-username/Happy-Vibe/issues) 中搜索是否已有相同问题
2. 如果没有，创建新 Issue，包含：
   - 问题描述
   - 复现步骤
   - 期望行为
   - 实际行为
   - 环境信息（操作系统、Python 版本等）

### 提出新功能

1. 创建 Issue 描述你的想法
2. 说明功能的使用场景
3. 等待讨论和确认后再开始开发

### 提交代码

1. Fork 项目
2. 创建功能分支
3. 编写代码和测试
4. 提交 Pull Request

---

## 开发流程

### 1. Fork 和克隆

```bash
# Fork 项目后克隆到本地
git clone https://github.com/your-username/Happy-Vibe.git
cd Happy-Vibe

# 添加上游仓库
git remote add upstream https://github.com/original/Happy-Vibe.git
```

### 2. 创建分支

```bash
# 从 main 创建功能分支
git checkout main
git pull upstream main
git checkout -b feature/your-feature-name
```

### 3. 开发和测试

```bash
cd vibehub

# 安装依赖
uv pip install -e ".[dev]"

# 编写代码...

# 运行测试
pytest tests/ -v

# 代码检查
ruff check src/ --fix
ruff format src/
```

### 4. 提交代码

```bash
git add .
git commit -m "feat: 添加新功能描述"
git push origin feature/your-feature-name
```

### 5. 创建 Pull Request

在 GitHub 上创建 PR，填写：
- 变更描述
- 关联的 Issue
- 测试情况

---

## 提交规范

### 提交信息格式

```
<类型>: <简短描述>

<详细描述（可选）>

<关联 Issue（可选）>
```

### 类型说明

| 类型 | 说明 |
|------|------|
| `feat` | 新功能 |
| `fix` | Bug 修复 |
| `docs` | 文档更新 |
| `style` | 代码格式（不影响功能） |
| `refactor` | 重构（不是新功能或修复） |
| `test` | 添加测试 |
| `chore` | 构建/工具变更 |

### 示例

```bash
# 新功能
git commit -m "feat: 添加公会战争系统"

# Bug 修复
git commit -m "fix: 修复能量计算溢出问题"

# 文档
git commit -m "docs: 更新 API 文档"

# 带详细描述
git commit -m "feat: 添加心流状态检测

- 实现 FlowDetector 类
- 支持 4 种心流状态
- 添加单元测试

Closes #123"
```

---

## 分支策略

```
main                 # 稳定版本
├── dev              # 开发分支
│   ├── feature/*    # 功能分支
│   └── fix/*        # 修复分支
└── release/*        # 发布分支
```

| 分支 | 用途 | 合并目标 |
|------|------|----------|
| `main` | 稳定版本 | - |
| `dev` | 开发集成 | `main` |
| `feature/*` | 新功能开发 | `dev` |
| `fix/*` | Bug 修复 | `dev` 或 `main` |

---

## 代码审查

### PR 检查清单

提交 PR 前请确认：

- [ ] 代码通过所有测试
- [ ] 新功能有对应测试
- [ ] 代码通过 ruff 检查
- [ ] 提交信息符合规范
- [ ] 更新了相关文档

### 审查标准

- 代码逻辑正确
- 符合项目代码规范
- 测试覆盖充分
- 无安全漏洞
- 性能合理

---

## 开发资源

- [用户指南](docs/user-guide.md)
- [开发者指南](docs/developer-guide.md)
- [设计文档](Note/Spec-Driven-Development.md)

---

## 联系方式

如有问题，可以通过以下方式联系：

- GitHub Issues
- 项目讨论区

再次感谢你的贡献！
