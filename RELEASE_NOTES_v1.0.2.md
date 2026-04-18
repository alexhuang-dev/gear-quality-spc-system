# v1.0.2 - Maintenance Refresh

This patch release keeps the public repository healthy after the first production-ready release.

## What Changed

- Upgraded GitHub Actions workflow dependencies:
  - `actions/checkout@v6`
  - `actions/setup-python@v6`
- Adjusted pytest temp/cache paths so Windows local runs do not collide with hidden temp directories.
- Ignored generated pytest runtime folders.
- Verified local test suite: `9 passed`.
- Verified GitHub Actions `tests` workflow on `main`: passed.

## 中文说明

这个版本是一次仓库维护更新，主要目标是让公开仓库、CI 和本地测试状态保持健康。

- 升级 GitHub Actions 依赖到新版 action。
- 修正 pytest 临时目录配置，减少 Windows 环境下的权限残留问题。
- 忽略测试运行时生成的临时目录。
- 本地测试通过：`9 passed`。
- GitHub Actions 主分支测试通过。

