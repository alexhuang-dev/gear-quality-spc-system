# Project Introduction | 项目介绍

## English

Gear Quality SPC System is an industrial quality analysis project built around one core decision: the system should be allowed to speak naturally, but it should not be allowed to improvise the numbers.

That is why the project is structured around a deterministic Python backend. SPC computation, rule evaluation, historical comparison, report artifacts, and consistency checks all live in code. Langflow is still part of the repository, but only as a presentation layer. The production path runs through FastAPI, LangGraph, SQLite, and the harness/test layer.

What makes the project interesting is not the number of features on the checklist. It is the boundary it draws. The project tries to answer a practical question: how do you keep the convenience of modern LLM-facing workflows without letting them take ownership of industrial facts?

My answer was to separate concerns very aggressively:

- code owns the calculations
- the workflow layer owns orchestration
- the language layer owns presentation

That separation is what gives the project its shape.

## 中文

齿轮质量 SPC 系统是一个工业质量分析项目，而它真正的出发点只有一个：系统可以把结果讲得自然，但不能把数字讲得随意。

所以这套项目从一开始就围绕确定性后端来搭。SPC 计算、规则判异、历史对比、报告产物和一致性校验都放在代码里完成。Langflow 仍然保留在仓库里，但它只承担展示层的角色；真正的生产主链路走的是 FastAPI、LangGraph、SQLite，以及 harness / test 这一层。

这个项目最有意思的地方，不在于功能列表有多长，而在于它对边界的处理。它想解决的是一个很现实的问题：在保留现代工作流和大模型交互便利性的同时，怎么不让这些层去接管工业场景里的事实判断。

我的做法是把职责拆得很明确：

- 代码负责计算
- 工作流层负责编排
- 语言层负责表达

项目最后长成什么样子，其实就是这个判断的结果。
