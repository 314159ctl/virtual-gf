# Contributing to virtual-gf

感谢你考虑为 virtual-gf 贡献代码！🎉

## 如何贡献

### 报告 Bug

1. 在 [Issues](https://github.com/314159ctl/virtual-gf/issues) 中搜索是否已有相同问题
2. 如果没有，新建 Issue，描述：
   - 你的运行环境（OS、Python 版本等）
   - 复现步骤
   - 期望行为 vs 实际行为
   - 相关截图或日志

### 提交代码

1. Fork 本仓库
2. 创建功能分支：
   ```bash
   git checkout -b feat/your-feature
   ```
3. 遵循现有的代码风格
4. 确保通过测试
5. 提交并推送：
   ```bash
   git commit -m "feat: 简要描述你的改动"
   git push origin feat/your-feature
   ```
6. 打开 Pull Request，描述你的改动

### Commit 规范

使用常见的前缀：
- `feat:` — 新功能
- `fix:` — Bug 修复
- `docs:` — 文档修改
- `refactor:` — 代码重构
- `chore:` — 构建/工具变更

## 开发环境

参考 [README.md](./README.md) 中的快速开始部分搭建本地开发环境。

## 代码风格

- Python: 遵循 PEP 8
- Vue/TypeScript: 使用 `vue-tsc` 进行类型检查