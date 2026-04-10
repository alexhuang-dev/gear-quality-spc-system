# Project Introduction | 项目介绍

## English

Gear Quality SPC System is a production-oriented industrial quality analytics project for gear inspection workflows.

It turns CSV-based inspection data into a deterministic SPC pipeline with:

- statistical process control computation
- Western Electric rule evaluation
- historical batch comparison
- machine-checkable harness validation
- reporting and chart generation
- alert payload generation

The production core is built in Python using FastAPI, LangGraph, SQLite, Streamlit, and pytest. Langflow is included only as an optional visual presentation layer.

This design intentionally separates:

- deterministic facts, which must be computed by code
- natural-language explanation, which can be handled by LLM-facing interfaces

That separation is the key reason the system is both explainable and engineering-safe.

## 中文

齿轮质量 SPC 系统是一个面向工业质量场景的生产导向型项目，用于把齿轮检测 CSV 数据转成真正可运行的质量分析流程。

系统核心能力包括：

- SPC 统计计算
- Western Electric 判异
- 历史批次对比
- Harness 机器校验
- 报告与图表生成
- 告警载荷生成

生产核心基于 Python，主要使用 FastAPI、LangGraph、SQLite、Streamlit 和 pytest。Langflow 只作为可选展示层，不是系统核心依赖。

这套设计最关键的一点，是明确区分了两类事情：

- 必须由代码保证正确性的确定性事实
- 可以由模型负责表达的自然语言说明

正因为做了这层分离，系统既能体现智能化，也能保持工程可信度。
