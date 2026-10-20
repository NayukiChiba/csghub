# 本机 Docker 开发环境

本次环境针对 Linux，使用当前 `csghub` 和同级 `csghub-server` 源码。前端和 Go 二进制编译后位于 `csghub/bin`，应用镜像为 `csghub-local:dev`。应用容器使用 host 网络；依赖容器使用 bridge 网络并通过本机端口供应用访问。

## 地址

| 服务 | 地址 |
|---|---|
| Portal | http://127.0.0.1:18090 |
| Server API | http://127.0.0.1:18080 |
| Casdoor | http://127.0.0.1:18000 |
| MinIO 控制台 | http://127.0.0.1:19001 |
| MinIO 文件下载 | http://127.0.0.1:19000 |
| User / DataViewer | 127.0.0.1:18088 / 127.0.0.1:18093 |
| PostgreSQL / Redis | 127.0.0.1:15432 / 127.0.0.1:16379 |
| Gitaly / NATS / Temporal | 127.0.0.1:18075 / 127.0.0.1:14222 / 127.0.0.1:17233 |

浏览器请使用 `127.0.0.1`，不要混用 `localhost` 和 Wi-Fi IP，以保持 OAuth 回调、Cookie 和对象存储链接一致。应用在 host 网络中监听配置端口，可能接受本机网卡上的连接；基础容器的端口只发布到回环地址。

本地演示账户 `demo` 的随机密码保存在 `deploy/dev/credentials.json`。此文件也包含本地 API token，请勿提交。Casdoor 的证书和初始化数据位于 `deploy/dev/casdoor/`；初始化只增加新记录，保留已有用户。

## 启停

从 `csghub` 根目录运行：

```bash
bin/local-up
bin/local-status

docker compose --env-file deploy/dev/.env -f docker-compose.dev.yml logs --tail 100 server user dataviewer portal
docker compose --env-file deploy/dev/.env -f docker-compose.dev.yml stop
```

命名卷保留数据库、Git 仓库和对象数据。不要使用 `down -v`，除非明确要清空本地数据。

## 编译本地改动

```bash
yarn --cwd frontend install --frozen-lockfile
yarn --cwd frontend build
go build -o bin/csghub-portal ./cmd/csghub-portal
(cd ../csghub-server && go build -tags ce -o ../csghub/bin/csghub-server ./cmd/csghub-server)
bin/local-up
```

`pack-runtime.py` 自动把本机编译产物所需的动态库与 CA 证书封装到镜像，避免宿主机 glibc 版本高于通用 Docker 运行时造成启动失败。修改源码后需要重新编译；此镜像只适用于当前 Linux/amd64 环境。

## Hugging Face 样本

下载文件位于 `data/huggingface`，总清单为 `manifest.json`。每个仓库保留上游 README（导入后的数据集原文在 `UPSTREAM_README.md`）、`SOURCE.json` 中的固定版本/来源/校验值，以及 `LOCAL_SAMPLE.md` 的本地样本说明。只下载部分文件：模型无大权重，数据集可能只有部分 split 或少量真实记录。

```bash
python bin/fetch-hf-samples.py
# 导出 Parquet 中的真实图像和音频小样本，并核验数据
 data/sample-tools/bin/python bin/prepare-samples.py
node bin/prepare-cards.cjs
# 首次创建 demo 本地用户使用真实 OAuth 登录
python bin/login-demo.py
# 经 CSGHub API 导入；可重复运行，已成功的相同文件会跳过
python bin/import-hf-samples.py
```

`fetch-hf-samples.py` 的基础列表之外，首次部署额外下载了 `hf-internal-testing/librispeech_asr_dummy` 的小型音频数据，并从 Dataset Viewer 获取了 UltraChat 的 30 条真实对话。精确下载内容以 `manifest.json` 为准。

日志位于 `data/logs`。原始开发 Compose 及 Gitaly 配置的备份位于本目录的 `*.original*` 文件。

`deploy/dev/credentials.json`、`server.docker.toml`、`portal.env`、
`casdoor/`、`.env`、编译后的 `bin/csghub-*` 以及 `data/` 均为本机实例文件，
其中包含随机凭据、私钥或运行数据，受 `.gitignore` 保护，不应提交到远端。

## 本地源码构建缺项修复

当前分支遗漏 `builder/memory`，从本地 Git 历史 `444dd173` 原样恢复 8 个文件（与 origin/main 一致），并把 `.gitignore` 的 `memory` 改为 `/memory`，避免再次忽略该源代码目录。已运行 `go test -tags ce ./builder/memory/...`，通过。Swagger 文件通过 `make swag` 生成，仅用于本地构建，不应提交。

数据集导入会跳过只有元数据、没有实际样本文件的仓库（例如此次的 ESC-50）；其下载原件仍保留在本地。模型是明确标记的元数据演示仓库。

## 本次验收（2026-10-20）

- 11 个容器已运行；具有健康检查的 PostgreSQL、Redis、Gitaly、Casdoor 均 healthy。
- Portal 首页、模型/数据集列表页、模型/数据集详情页及静态 JS 资源均返回 HTTP 200。
- `python bin/login-demo.py`：真实 Casdoor OAuth 登录、API 回调、Portal 会话建立成功。
- 已导入 5 个模型、7 个数据集；`python bin/verify-samples.py` 对 107 个文件逐一从服务下载并比较 SHA256，全部一致，合计 95,455,933 字节。
- 7 个数据集预览任务全部完成；逐一验证预览返回真实记录。示例行数：Iris 150，提示词 2,533，UltraChat 30，MNIST 测试集 10,000，IMDB 测试集 25,000，SQuAD 验证集 10,570，LibriSpeech 73。
- `data/huggingface/service-validation.json` 保存文件下载验收结果；`preview-validation.json` 保存预览验收结果。

为使样本开箱可预览，CSV/JSONL 保留原文件，并额外生成 `preview/*.parquet`；来源与派生关系在 SOURCE.json 中记录。提示词 CSV 使用 LFS 存储，保留原始 CRLF 字节；其 `.gitattributes.local` 会在导入时映射为仓库的 `.gitattributes`。派生 Parquet 使用兼容版本及简化统计元数据。下载目录中原始模型不含大权重，因此不作为直接推理部署包。

### 启动过程修复

除了补齐 memory 包，还修复了 `dataviewer/component/dataset_viewer.go` 的单文件预览：加载仓库后，将实际 `RepoID` 和 `Migrated` 传给 LFS 路径构造，避免新仓库被当成旧布局而返回对象不存在。权限检查不变；回归测试同时覆盖旧 LFS 和按仓库分隔的 LFS 路径。回归测试修复前失败，修复后通过。结构检查确认改动复用邻近 Rows/GetCatalog 的参数赋值模式，无需扩大重构。

Gitaly 的容器内端口也改为 18075，与客户端声明的地址一致，并同步修改健康检查，保证 Gitaly 创建转换分支时的内部回连正常。数据预览所需的 DuckDB 0.9.2 `httpfs`、`json` 扩展及对应动态库已封装到应用镜像。

### 验证命令和范围

```bash
# 均通过
go test -tags ce ./builder/memory/...
go test -tags ce ./dataviewer/...
go build -tags ce -o ../csghub/bin/csghub-server ./cmd/csghub-server
git diff --check
```

以上 Go 命令在 `csghub-server` 中运行。Portal 已通过 `yarn --cwd frontend build` 与 `go build -o bin/csghub-portal ./cmd/csghub-portal`。

仓库 AGENTS.md 提到的 `make test_all` 和 `make lint_all` 在当前 Makefile 中没有对应 target；本机也未安装 golangci-lint。已尝试 `go test -tags ee ./dataviewer/...` 和 `go test -tags saas ./dataviewer/...`，两者均因当前仓库缺少相应构建标签下的 `registerDatabaseHooks` 和 deploy mock 实现而无法编译。当前部署和已通过的测试为 CE，不声称 EE/SaaS 或完整仓库测试通过。

Casdoor 初始化配置参考与镜像版本匹配的[官方模板](https://github.com/casdoor/casdoor/blob/v1.733.0/init_data.json.template)；DuckDB 扩展按[官方安装方式](https://duckdb.org/docs/current/extensions/installing_extensions)预装。
