# paper-rank-proxy

`paper-rank-proxy` 是一个基于 FastAPI 的 EasyScholar 期刊等级查询代理服务，使用 SQLite 做本地缓存。

English: [README.md](README.md)

## 功能

- 按期刊名称查询 EasyScholar 官方开放接口。
- 将查询结果缓存到 SQLite。
- 支持单期刊查询、批量查询、强制刷新。
- 使用 Bearer token 保护查询接口。
- 完整保留 `officialRank.all`、`officialRank.select`、`customRank`，并额外抽取常用字段。

本项目使用的 EasyScholar 官方接口：

```text
GET https://www.easyscholar.cc/open/getPublicationRank
```

上游请求只传：

```text
secretKey
publicationName
```

EasyScholar 官方接口未说明支持 ISSN-only 查询，因此本代理会拒绝只有 ISSN 的请求。

## 环境要求

- Python 3.11+
- 不需要单独安装 SQLite 服务端。Python 自带 SQLite 支持。

## 安装

```bash
python -m venv .venv
.venv\Scripts\activate
python -m pip install -e .
```

Linux/macOS：

```bash
source .venv/bin/activate
```

## 配置

复制 `.env.example` 为 `.env`：

```env
EASYSCHOLAR_SECRET_KEY=
EASYSCHOLAR_API_URL=https://www.easyscholar.cc/open/getPublicationRank
RANK_PROXY_TOKEN=
RANK_CACHE_TTL_DAYS=180
RANK_CACHE_NEGATIVE_TTL_DAYS=7
EASYSCHOLAR_RATE_LIMIT_PER_SECOND=2
RANK_PROXY_DATABASE_URL=sqlite:///./data/rank_cache.sqlite3
RANK_BATCH_MAX_SIZE=100
```

不要提交 `.env`、本地数据库文件或日志。

## 启动

```bash
uvicorn app.main:app --reload
```

服务启动时会自动创建 SQLite 表。

## 鉴权

除 `/health` 外，查询接口都需要：

```http
Authorization: Bearer <RANK_PROXY_TOKEN>
```

## 接口

### 健康检查

```http
GET /health
```

### 单期刊查询

```http
GET /rank?publication_name=Applied%20Energy
Authorization: Bearer <RANK_PROXY_TOKEN>
```

可选参数：

```text
force_refresh=true
```

### 批量查询

```http
POST /rank/batch
Content-Type: application/json
Authorization: Bearer <RANK_PROXY_TOKEN>
```

```json
{
  "items": [
    {
      "publication_name": "IEEE Transactions on Power Systems"
    },
    {
      "publication_name": "Applied Energy"
    }
  ],
  "force_refresh": false
}
```

### 强制刷新

```http
POST /rank/refresh
Content-Type: application/json
Authorization: Bearer <RANK_PROXY_TOKEN>
```

```json
{
  "publication_name": "Applied Energy"
}
```

## 返回结构

```json
{
  "publication_name": "Applied Energy",
  "normalized_name": "applied energy",
  "source": "easyscholar",
  "status": "ok",
  "cache_hit": true,
  "journal_rank": {
    "official_rank_all": {
      "sci": "Q1",
      "sciif": "12.2",
      "sciUp": "工程技术1区",
      "eii": "EI"
    },
    "official_rank_select": {},
    "custom_rank": null,
    "sci": "Q1",
    "cas_zone": "工程技术1区",
    "cas_small": "工程：化工1区/能源与燃料2区。",
    "cas_top": "工程技术TOP",
    "impact_factor": 12.2,
    "five_year_if": 12.1,
    "ei": "EI"
  }
}
```

## 字段映射

完整 EasyScholar 字典会保留在：

- `journal_rank.official_rank_all`
- `journal_rank.official_rank_select`

常用字段映射：

| 返回字段 | EasyScholar 字段 |
| --- | --- |
| `sci` | `sci` |
| `ssci` | `ssci` |
| `impact_factor` | `sciif` |
| `five_year_if` | `sciif5` |
| `cas_zone` | `sciUp`，回退 `sciBase` |
| `cas_small` | `sciUpSmall` |
| `cas_top` | `sciUpTop` |
| `ei` | `eii` |
| `cscd` | `cscd` |
| `pku_core` | `pku` |
| `cssci` | `cssci` |
| `esi` | `esi` |
| `warning` | `sciwarn` |

## SQLite

默认数据库：

```text
./data/rank_cache.sqlite3
```

主要表：

- `journal_rank_cache`：缓存期刊等级结果。
- `rank_query_log`：记录查询类型、缓存命中、状态和上游诊断信息。

## 开发说明

- 尽量保持 API 返回结构向后兼容。
- 配置项或接口行为变化时，同步更新 README。
- 不要记录完整 EasyScholar 请求 URL，因为上游 key 位于 query 参数中。

## License

MIT
