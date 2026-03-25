# Docker 启动（后端:8000 + 前端:3000）

```bash
docker compose up webui-backend webui-frontend
```

# 本地开发

# 后端

```bash
pip install -r webui/requirements.txt
uvicorn webui.backend.main:app --reload --port 8000
```

# 前端

```bash
cd webui/frontend && npm install && npm run dev
```
