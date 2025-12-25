# Build and Publish Guide (UV Native)

Claude Agent Framework 使用 UV 的原生构建和发布功能，无需额外工具。

## Quick Start

### Prerequisites

安装 UV:
```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```

### Build Package

```bash
# 使用 uv 构建
uv build

# 或使用 Makefile
make build
```

输出位置：`dist/`
- `claude-agent-framework-X.Y.Z.tar.gz` (源码分发)
- `claude_agent_framework-X.Y.Z-py3-none-any.whl` (wheel)

### Publish to TestPyPI

```bash
# 使用 uv 发布
uv publish --index-url https://test.pypi.org/legacy/

# 或使用 Makefile
make publish-test
```

### Publish to PyPI

```bash
# 使用 uv 发布
uv publish

# 或使用 Makefile
make publish-prod
```

## UV Build & Publish 命令

UV 提供了完整的构建和发布功能：

```bash
# 构建包
uv build                # 构建 wheel 和源码分发
uv build --wheel        # 只构建 wheel
uv build --sdist        # 只构建源码分发

# 发布包
uv publish                                          # 发布到 PyPI
uv publish --index-url URL                          # 发布到自定义 index
uv publish --index-url https://test.pypi.org/legacy/  # 发布到 TestPyPI
```

## Authentication

### PyPI Token

获取 token:
1. 访问 https://pypi.org/manage/account/
2. 创建 API token
3. 复制 token (只显示一次)

### 配置认证

**方法 1: 环境变量**
```bash
export UV_PUBLISH_USERNAME=__token__
export UV_PUBLISH_PASSWORD=pypi-AgEIcHlwaS5vcmc...
```

**方法 2: Keyring (推荐)**
UV 支持系统 keyring:
```bash
# UV 会自动使用系统 keyring
# macOS: Keychain
# Linux: Secret Service / KWallet
# Windows: Credential Manager
```

**方法 3: 交互式输入**
不设置认证信息时，UV 会提示输入：
```bash
uv publish
# Username: __token__
# Password: [输入你的 token]
```

## Makefile 命令

项目提供了简化的 Makefile 命令：

```bash
make build           # 构建分发包
make build-clean     # 清理并重新构建
make publish-test    # 发布到 TestPyPI
make publish-prod    # 发布到 PyPI
```

## Complete Workflow

### Development

```bash
# 1. 同步依赖
make sync

# 2. 安装开发依赖
make dev

# 3. 开发代码
# ...

# 4. 运行测试
make test

# 5. 代码检查
make lint
make format
```

### Release

```bash
# 1. 更新版本号
# 编辑 pyproject.toml: version = "X.Y.Z"

# 2. 清理并构建
make build-clean

# 3. 检查构建产物
ls -lh dist/

# 4. 发布到 TestPyPI (测试)
make publish-test

# 5. 测试安装
pip install -i https://test.pypi.org/simple/ claude-agent-framework

# 6. 发布到 PyPI (生产)
make publish-prod

# 7. 创建 git tag
git tag vX.Y.Z
git push origin vX.Y.Z
```

## Advanced Usage

### Build Options

```bash
# 指定输出目录
uv build --out-dir ./build_output

# 只构建 wheel
uv build --wheel

# 只构建源码分发
uv build --sdist

# 详细输出
uv build --verbose
```

### Publish Options

```bash
# 发布到 TestPyPI
uv publish --index-url https://test.pypi.org/legacy/

# 跳过已存在的文件
uv publish --skip-existing

# 详细输出
uv publish --verbose

# 指定要发布的文件
uv publish dist/claude_agent_framework-0.3.0-py3-none-any.whl
```

## GitHub Actions

项目包含自动发布工作流 (`.github/workflows/publish.yml`):

**自动触发**:
- 创建 GitHub Release → 自动构建和发布

**手动触发**:
```bash
gh workflow run publish.yml -f environment=test   # 发布到 TestPyPI
gh workflow run publish.yml -f environment=prod   # 发布到 PyPI
```

工作流使用 UV 进行构建：
```yaml
- name: Build distribution
  run: |
    cd claude_agent_framework
    uv build
```

## Troubleshooting

### "uv not found"
```bash
# 安装 UV
curl -LsSf https://astral.sh/uv/install.sh | sh

# 添加到 PATH
export PATH="$HOME/.cargo/bin:$PATH"
```

### "Authentication failed"
```bash
# 检查环境变量
echo $UV_PUBLISH_USERNAME
echo $UV_PUBLISH_PASSWORD

# 或使用交互式输入
uv publish  # 会提示输入用户名和密码
```

### "Package already exists"
PyPI 不允许重复上传相同版本。需要：
1. 更新 `pyproject.toml` 中的版本号
2. 重新构建：`make build-clean`
3. 重新发布

### "Invalid distribution"
```bash
# 检查构建产物
ls -lh dist/

# 重新构建
make build-clean
```

## Version Management

版本号在 `pyproject.toml` 中管理：

```toml
[project]
name = "claude-agent-framework"
version = "0.3.0"  # 更新这里
```

推荐使用语义化版本 (SemVer):
- `0.3.0` → `0.3.1` - 补丁版本（bug 修复）
- `0.3.0` → `0.4.0` - 次要版本（新功能）
- `0.3.0` → `1.0.0` - 主要版本（破坏性变更）

## UV vs Traditional Tools

| 功能 | 传统方式 | UV 方式 |
|------|---------|---------|
| 构建 | `python -m build` | `uv build` |
| 发布 | `twine upload dist/*` | `uv publish` |
| 依赖 | pip, build, twine | 仅需 uv |
| 配置 | ~/.pypirc | 环境变量或 keyring |
| 速度 | 慢 | 快 |

## See Also

- [UV Documentation](https://docs.astral.sh/uv/)
- [UV Build Guide](https://docs.astral.sh/uv/guides/publish/)
- [PyPI Help](https://pypi.org/help/)
- [Semantic Versioning](https://semver.org/)
