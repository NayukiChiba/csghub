# dev 分支开发环境

当前 Linux 本机环境使用 Docker 运行应用和依赖，统一通过 `127.0.0.1` 访问。
启动、端口、演示账户、源码构建和 Hugging Face 样本导入请参见 [LOCAL.md](LOCAL.md)。
下面保留的是原先“Docker 依赖 + 宿主机应用”的开发说明。

这套环境只把稳定依赖放进 Docker；需要改代码的 Portal、CSGHub Server、User Server 和 DataViewer 均在宿主机运行。这样前端断点、Go 断点和热更新不会被容器构建打断。

## 目录约定

Compose 会只读挂载 Server 仓库中的 Casdoor 初始化数据，因此两个仓库需要同级放置：

```text
D:\Code\
├─ csghub\
└─ csghub-server\
```

如果 Server 仓库不在该位置，请修改 `docker-compose.dev.yml` 中 Casdoor 的挂载路径。

## 启动 Docker 基础设施

在 `csghub` 根目录执行：

```powershell
Copy-Item deploy/dev/.env.example deploy/dev/.env
docker compose --env-file deploy/dev/.env -f docker-compose.dev.yml up -d
docker compose --env-file deploy/dev/.env -f docker-compose.dev.yml ps
```

需要查看 Temporal 工作流时，额外启用工具 profile：

```powershell
docker compose --env-file deploy/dev/.env -f docker-compose.dev.yml --profile tools up -d
```

默认访问地址：

| 服务 | 地址 |
| --- | --- |
| PostgreSQL | `127.0.0.1:15432` |
| Redis | `127.0.0.1:16379` |
| MinIO API / 控制台 | `http://127.0.0.1:19000` / `http://127.0.0.1:19001` |
| Gitaly | `tcp://127.0.0.1:18075` |
| NATS / 监控 | `127.0.0.1:14222` / `http://127.0.0.1:18222` |
| Temporal | `127.0.0.1:17233` |
| Casdoor | `http://127.0.0.1:18000` |
| Temporal UI（可选） | `http://127.0.0.1:18180` |

## 初始化并启动 Server 链路

下面的命令都在 `csghub-server` 根目录执行。首次启动先初始化数据库：

> Windows 注意：Server 和 DataViewer 依赖 DuckDB、Kafka 的 CGO 实现。若 `go env CGO_ENABLED` 为 `0`，会出现 `undefined: kafka.Producer`、`undefined: conn` 等编译错误。建议在 WSL2 中运行下面的 Go 命令；或者先安装可用的 C/C++ 工具链，再设置 `CGO_ENABLED=1`。Docker 基础设施仍可由 Windows Docker Desktop 提供。

```powershell
go run ./cmd/csghub-server --config=../csghub/deploy/dev/server.local.toml migration init
go run ./cmd/csghub-server --config=../csghub/deploy/dev/server.local.toml migration migrate
```

随后分别打开三个终端：

```powershell
# 核心 API，端口 8080
go run ./cmd/csghub-server --config=../csghub/deploy/dev/server.local.toml start server

# 登录和用户服务，端口 8088；需要测试登录接口时启动
go run ./cmd/csghub-server --config=../csghub/deploy/dev/server.local.toml user launch

# 数据预览 API 与对应 Temporal worker，端口 8093
go run ./cmd/csghub-server --config=../csghub/deploy/dev/server.local.toml dataviewer launch
```

Portal 的 `.env` 至少保持以下两项与 Server 一致：

```dotenv
CSGHUB_PORTAL_STARHUB_BASE_URL=http://localhost:8080
CSGHUB_PORTAL_STARHUB_API_KEY=f3a7b9c1d6e5f8e2a1b5d4f9e6a2b8d7c3a4e2b1d9f6e7a8d2c5a7b4c1e3f5b8a1d4f9b7d6e2f8a5d3b1e7f9c6a8b2d1e4f7d5b6e9f2a4b3c8e1d7f995hd82hf
```

前端开发仍使用项目原有方式：在 `frontend` 中执行 `yarn dev_build` 监听构建，同时在 Portal 根目录运行 Go 服务或 VS Code 调试配置。

## 五项任务如何隔离

| 任务 | 本地需要启动 | 主要改动仓库/模块 | Docker 依赖 |
| --- | --- | --- | --- |
| 1. 自定义标签参与筛选 | Portal + Server | Portal 标签筛选、Server 标签查询 | PostgreSQL、Redis |
| 2. 修复内置 DataViewer | Portal + Server + DataViewer | Server `dataviewer`、Portal 预览组件 | PostgreSQL、Redis、Gitaly、MinIO、Temporal |
| 3. 新增预览标签页 | Portal + Server + DataViewer | 新解析 API 与新前端页签 | 同任务 2 |
| 4. 浏览器直接下载 | Portal + Server | 下载路由、鉴权、Range/流式响应 | Gitaly、MinIO、PostgreSQL |
| 5. 自然语言搜索 | Portal + Server | 搜索接口、索引与 Agent 编排 | PostgreSQL、Redis、NATS；语义检索方案确定后再增加向量库 |

建议每项任务使用独立 feature 分支，但共享这套 `csghub-dev` 基础设施。测试数据都在 Compose 命名卷内，不会写入源码目录，也不会与默认项目名的数据卷混用。

## 停止与清理

停止容器但保留测试数据：

```powershell
docker compose --env-file deploy/dev/.env -f docker-compose.dev.yml down
```

只有确定不再需要本分支数据库、对象和 Git 仓库时，才执行：

```powershell
docker compose --env-file deploy/dev/.env -f docker-compose.dev.yml down -v
```

`down -v` 会永久删除该 Compose 项目的命名卷数据。
