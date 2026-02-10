# Happy Vibe Hub

Vibe-Coding 游戏化平台本地服务。

## 安装

```bash
pip install -r requirements.txt
```

## 运行

```bash
python -m src.main
```

服务运行在 http://127.0.0.1:8765

## 测试

```bash
pytest
```

## API 端点

- `GET /health` - 健康检查
- `GET /api/health` - API 健康检查（兼容路径）
