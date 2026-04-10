# 齿轮质量 SPC 系统

![Python](https://img.shields.io/badge/Python-Production-blue)
![FastAPI](https://img.shields.io/badge/API-FastAPI-009688)
![LangGraph](https://img.shields.io/badge/流程编排-LangGraph-black)
![Status](https://img.shields.io/badge/状态-v1.0.0-success)

[English](README.md)

这个项目最开始不是从“我要做一个多智能体系统”出发的，而是从一个很朴素的工程判断出发的：质量分析里有些部分可以写得灵活，但数字本身不能含糊。

所以我一开始就把边界划得很清楚。像 SPC 指标、控制限、历史批次差值、状态判断，这些必须由确定性的 Python 代码负责；表达层可以更自然，甚至可以接 Langflow 做演示，但它不能反过来定义事实。也正因为这样，这个项目最后长成了一套后端优先的质量分析系统，而不是一个围着提示词堆起来的工作流 demo。

它现在做的事情很直接：把齿轮检测 CSV 数据接进来，跑一套可重复的 SPC 分析流程，接上历史记录，生成报告和图表，再用一层 harness 去检查最终输出有没有把数字说歪。

![Architecture Overview](docs/assets/architecture-overview.svg)

## 设计判断

### 1. 先把“不能错”的部分收回到代码里

这个项目里最重要的决定，不是用了哪个框架，而是决定哪些事情绝不能交给语言模型。  
因此 `core/` 里负责的是确定性部分：SPC 计算、Western Electric 判异、历史对比、状态分级、报告产物和校验逻辑。这样做的好处很简单：以后前端怎么换、提示词怎么改，关键数值都不会跟着漂。

### 2. 保留 Langflow，但把它放在合适的位置

我没有把 Langflow 删掉，因为它对演示和工作流展示确实有价值。但我也没有让它成为系统核心。  
这套系统真正的主链路是 `FastAPI + LangGraph + SQLite + Streamlit`。Langflow 只是一个入口，适合汇报、面试和业务演示，不应该承担事实裁决。

### 3. 校验不是最后补的，而是一开始就放进去的

很多项目会先把流程跑通，再考虑稳定性。我的处理方式反过来一点：只要系统要生成质量结论，就必须有一套东西去检查“最后写出来的话”和“前面算出来的数”是不是一致。  
所以这个仓库里从第一版开始就带着 harness、golden case 和回归测试。

## 仓库结构

```text
core/                  SPC、历史、图表、报告、告警、harness 逻辑
graph/                 LangGraph 编排层，带确定性回退
api/                   FastAPI 服务层
harness/               黄金样本与回归辅助
services/              自动处理服务
dashboard/             Streamlit 看板
langflow_integration/  Langflow 自定义组件
tests/                 单元测试与回归样本
data/specs/            默认规格限配置
```

## 当前做到哪里

现在这套系统已经把软件侧的主干搭完整了：

- 确定性 SPC 计算
- Western Electric 8 条规则
- SQLite 历史记忆
- 报告和图表生成
- webhook 告警载荷
- harness 一致性校验
- dashboard 展示
- 可选 Langflow 工作流入口

它目前没有假装解决的，是工厂现场那部分：真实规格限归属、MES/ERP/PLC 对接、以及产线数据契约。这些本来就不应该在一个通用仓库里硬写死。

## 运行方式

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

### Docker

```bash
cp .env.example .env
docker compose -f docker-compose.production.yml up --build -d
```

## Langflow 入口

如果要看可视化工作流版本，用这两个文件：

- `New Flow - v9.3 api-frontend-prompt-merge-friendly.json`
- `langflow_integration/gear_spc_component.py`

它调用的是后端 API。也就是说，Langflow 是前台，不是地基。

## 接口

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

## 相关文档

- `PRODUCTION_DEPLOYMENT.md`
- `FINAL_ARCHITECTURE.md`
- `PROJECT_INTRO_BILINGUAL.md`
- `INTERVIEW_GUIDE.zh-CN.md`
- `SHOWCASE.md`
