# 齿轮质量 SPC 系统

[English](README.md)

这是一个面向生产场景的齿轮质量分析系统，用来把齿轮检测 CSV 数据真正变成可运行、可追踪、可验证的质量分析流程。系统核心基于**确定性 Python 计算**，外层结合 `LangGraph` 编排、`FastAPI` 服务、`Harness` 机器校验、图表报告，以及可选的 `Langflow` 展示入口。

## 项目定位

这个项目不是“让大模型算数字”，而是把数字计算、历史对比、报告生成、规则校验这些事情放回到稳定的软件层来做。

它的目标是：

- 解析齿轮检测 CSV 数据
- 稳定计算 SPC 指标
- 做历史批次对比
- 自动生成报告和图表
- 用 Harness 校验最终结果前后一致
- 对接告警和后续自动化流程

## 它是不是纯 Python 版本

**是的，生产核心是纯 Python。**

当前生产主链路包括：

- `FastAPI`：提供分析接口
- `LangGraph`：流程编排，且带确定性回退
- `SQLite`：保存历史记录
- `Streamlit`：看板展示
- `pytest` + 黄金样本：回归测试

也就是说，**即使不用 Langflow，这套系统依然能完整运行。**

## 需不需要借助 Langflow

**不需要。**

Langflow 在这套架构里是**可选展示层**，主要作用是：

- 做可视化工作流演示
- 给面试或汇报场景一个更直观的入口
- 把后端结构化结果交给 Agent 做说明性输出

但它不是系统核心，也不是事实来源。  
真正的事实来源是后端 Python API。

## 当前系统能做什么

- 解析齿轮检测 CSV 数据
- 确定性计算 SPC 指标
- 执行 Western Electric 8 条规则
- 将历史运行结果持久化到 SQLite
- 自动做当前批次与历史批次对比
- 生成 JSON / HTML / SVG 报告
- 支持可选 PDF 生成
- 输出机器可校验的 Harness 结果
- 生成 webhook 预警载荷
- 支持自动监听目录并处理新 CSV
- 提供 Streamlit 质量看板

## 系统结构

```text
core/                  核心确定性计算层：SPC、历史、图表、报告、告警、Harness
graph/                 LangGraph 编排层，带顺序回退
api/                   FastAPI 服务层
harness/               黄金样本与回归测试工具
services/              自动处理服务
dashboard/             Streamlit 看板
langflow_integration/  Langflow 自定义组件
tests/                 单元测试与黄金样本测试
data/specs/            默认规格限配置
```

## 两种使用方式

### 1. 纯 Python 生产模式

直接使用：

- FastAPI
- Dashboard
- Auto Runner

这才是推荐的生产模式。

### 2. Langflow 展示模式

使用：

- `New Flow - v9.3 api-frontend-prompt-merge-friendly.json`
- `langflow_integration/gear_spc_component.py`

这时 Langflow 只是展示和说明层，后端 API 仍然是唯一真相来源。

## 快速启动

### 本地运行

```powershell
python -m venv .venv
.\.venv\Scripts\python -m pip install -r requirements.txt
powershell -ExecutionPolicy Bypass -File .\start_production_stack.ps1
```

启动后可访问：

- API 文档：[http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs)
- 就绪检查：[http://127.0.0.1:8000/ready](http://127.0.0.1:8000/ready)
- Dashboard：[http://127.0.0.1:8501](http://127.0.0.1:8501)

### Docker 部署

```bash
cp .env.example .env
docker compose -f docker-compose.production.yml up --build -d
```

## API 接口

- `GET /health`
- `GET /ready`
- `GET /config/public`
- `POST /analyze`
- `POST /analyze-file`
- `GET /history`
- `GET /report/{run_id}`
- `GET /dashboard/summary`
- `POST /regression`
- `POST /alerts/test`

## 测试

```powershell
.\.venv\Scripts\python -m pytest tests -q
```

## 真正上线前还要补什么

软件架子已经是生产导向的，但真进工厂还要补外部条件：

- 真实规格限
- 真实 webhook 告警地址
- 真实 MES / ERP / PLC 对接要求

换句话说：

**现在的软件系统已经能跑、能测、能演示、能部署。**  
**后面要不要变成真实产线系统，取决于你接入的现场数据和现场系统。**

## 相关文档

- `PRODUCTION_DEPLOYMENT.md`
- `FINAL_ARCHITECTURE.md`
- `langflow_integration/SETUP.md`
