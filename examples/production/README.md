# Production Examples

Production-grade examples demonstrating Claude Agent Framework's 7 architectures in real-world business scenarios.

## Example List

| Example | Architecture | Business Scenario | Status |
|---------|--------------|-------------------|--------|
| [01_competitive_intelligence](01_competitive_intelligence/) | Research | SaaS Competitive Analysis | ✅ Complete |
| [02_pr_code_review](02_pr_code_review/) | Pipeline | Automated PR Review | 🚧 In Progress |
| [03_marketing_content](03_marketing_content/) | Critic-Actor | Marketing Copy Optimization | 📋 Planned |
| [04_it_support](04_it_support/) | Specialist Pool | IT Support Routing | 📋 Planned |
| [05_tech_decision](05_tech_decision/) | Debate | Technical Decision Support | 📋 Planned |
| [06_code_debugger](06_code_debugger/) | Reflexion | Adaptive Debugging | 📋 Planned |
| [07_codebase_analysis](07_codebase_analysis/) | MapReduce | Large Codebase Analysis | 📋 Planned |

## Quick Start

### 1. Install Framework

```bash
cd /path/to/claude-agent-framework
pip install -e ".[all]"
```

### 2. Set API Key

```bash
export ANTHROPIC_API_KEY="your-api-key"
```

### 3. Run Example

```bash
# Navigate to example directory
cd examples/production/01_competitive_intelligence

# Run
python main.py
```

## Example Features

Each example includes:

- ✅ **Complete Runnable Code** - Main program, config files, custom components
- ✅ **Error Handling** - Comprehensive exception handling and user-friendly error messages
- ✅ **Logging** - Structured logs and progress indicators
- ✅ **Test Coverage** - Unit tests, integration tests, end-to-end tests
- ✅ **Complete Documentation** - README (English + Chinese), architecture docs, customization guide

## Shared Utilities

The `common/` directory provides shared utilities for all examples:

- **load_yaml_config** - YAML configuration loading
- **setup_logging** - Logging configuration
- **ResultSaver** - Unified result saving interface (JSON/Markdown/PDF)
- **validate_config** - Configuration validation
- **ConfigurationError / ExecutionError** - Custom exceptions

## Architecture Comparison

| Architecture | Parallelism | Iteration | Best For |
|--------------|-------------|-----------|----------|
| **Research** | High | No | Comprehensive research, data collection |
| **Pipeline** | None | No | Clear sequential tasks |
| **Critic-Actor** | None | Yes | Quality iteration needed |
| **Specialist Pool** | Medium | No | Domain expertise required |
| **Debate** | None | Structured | Balanced analysis needed |
| **Reflexion** | None | Yes | Complex problem solving |
| **MapReduce** | High | No | Large-scale data processing |

## Related Documentation

- [Production Examples Design Document](../../docs/PRODUCTION_EXAMPLES_DESIGN.md) - Detailed design specifications
- [Best Practices Guide](../../docs/BEST_PRACTICES.md) - Architecture usage guide
- [Framework Documentation](../../README.md) - Framework overview

## License

MIT License
