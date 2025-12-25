# Production Examples

生产级示例展示了 Claude Agent Framework 的7个架构在真实业务场景中的应用。

## 示例列表

| 示例 | 架构 | 业务场景 | 状态 |
|------|------|----------|------|
| [01_competitive_intelligence](01_competitive_intelligence/) | Research | SaaS 竞品分析 | ✅ 已完成 |
| [02_pr_code_review](02_pr_code_review/) | Pipeline | 自动化 PR 审查 | ✅ 已完成 |
| [03_marketing_content](03_marketing_content/) | Critic-Actor | 营销文案优化 | ✅ 已完成 |
| [04_it_support](04_it_support/) | Specialist Pool | IT 支持路由 | ✅ 已完成 |
| [05_tech_decision](05_tech_decision/) | Debate | 技术决策支持 | ✅ 已完成 |
| [06_code_debugger](06_code_debugger/) | Reflexion | 自适应调试 | ✅ 已完成 |
| [07_codebase_analysis](07_codebase_analysis/) | MapReduce | 大规模代码库分析 | ✅ 已完成 |

## 快速开始

### 1. 安装框架

```bash
cd /path/to/claude-agent-framework
pip install -e ".[all]"
```

### 2. 设置 API Key

```bash
export ANTHROPIC_API_KEY="your-api-key"
```

### 3. 运行示例

```bash
# 进入示例目录
cd examples/production/01_competitive_intelligence

# 运行
python main.py
```

## 示例特性

每个示例都包含：

- ✅ **完整可运行代码** - 包含主程序、配置文件、自定义组件
- ✅ **错误处理** - 完善的异常处理和用户友好的错误提示
- ✅ **日志记录** - 结构化日志和进度指示器
- ✅ **测试覆盖** - 单元测试、集成测试、端到端测试
- ✅ **完整文档** - README（中英双语）、架构说明、定制指南

## 共享工具

`common/` 目录提供所有示例共享的工具：

- **load_yaml_config** - YAML 配置加载
- **setup_logging** - 日志配置
- **ResultSaver** - 统一的结果保存接口（JSON/Markdown/PDF）
- **validate_config** - 配置验证
- **ConfigurationError / ExecutionError** - 自定义异常

## 架构对比

| 架构 | 并行度 | 迭代特性 | 最佳场景 |
|------|--------|----------|----------|
| **Research** | 高 | 无 | 综合性研究、数据收集 |
| **Pipeline** | 无 | 无 | 明确的阶段性任务 |
| **Critic-Actor** | 无 | 是 | 需要质量迭代 |
| **Specialist Pool** | 中 | 无 | 需要领域专业知识 |
| **Debate** | 无 | 结构化 | 需要平衡分析 |
| **Reflexion** | 无 | 是 | 复杂问题解决 |
| **MapReduce** | 高 | 无 | 大规模数据处理 |

## 相关文档

- [生产级示例设计文档](../../docs/PRODUCTION_EXAMPLES_DESIGN_CN.md) - 详细设计规范
- [最佳实践指南](../../docs/BEST_PRACTICES_CN.md) - 架构使用指南
- [框架文档](../../README_CN.md) - 框架总览

## License

MIT License
