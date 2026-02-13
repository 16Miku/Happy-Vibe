# Happy Vibe Monitor

桌面监控器 - 系统托盘应用，用于追踪编码活动并与 VibeHub 服务通信。

## 功能

- 系统托盘图标，显示当前状态
- 桌面通知（心流状态、成就、能量获取）
- 自动追踪编码活动
- 与 VibeHub 服务实时通信

## 安装

```bash
cd monitor
uv venv
uv pip install -e ".[dev]"
```

## 运行

```bash
happy-vibe-monitor
```

## 测试

```bash
pytest tests/ -v
```
