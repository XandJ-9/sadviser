#!/bin/bash
# 测试运行脚本

set -e

# 颜色定义
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${GREEN}======================================${NC}"
echo -e "${GREEN}sadviser 测试运行脚本${NC}"
echo -e "${GREEN}======================================${NC}"
echo ""

# 检查Python版本
PYTHON_VERSION=$(python --version 2>&1 | awk '{print $2}')
echo -e "Python版本: ${YELLOW}$PYTHON_VERSION${NC}"
echo ""

# 检查是否安装了uv
if command -v uv &> /dev/null; then
    PACKAGE_MANAGER="uv"
    echo -e "使用包管理器: ${YELLOW}uv${NC}"
else
    PACKAGE_MANAGER="pip"
    echo -e "使用包管理器: ${YELLOW}pip${NC}"
fi
echo ""

# 安装测试依赖
echo -e "${GREEN}[1/5] 安装测试依赖...${NC}"
if [ "$PACKAGE_MANAGER" = "uv" ]; then
    uv sync --extra test
else
    pip install pytest pytest-asyncio pytest-cov pytest-xdist pytest-mock
fi
echo -e "${GREEN}✓ 依赖安装完成${NC}"
echo ""

# 运行测试
echo -e "${GREEN}[2/5] 运行测试...${NC}"
if [ "$PACKAGE_MANAGER" = "uv" ]; then
    uv run pytest "$@"
else
    pytest "$@"
fi
TEST_EXIT_CODE=$?
echo ""

# 如果测试通过,生成覆盖率报告
if [ $TEST_EXIT_CODE -eq 0 ]; then
    echo -e "${GREEN}[3/5] 生成测试覆盖率报告...${NC}"
    if [ "$PACKAGE_MANAGER" = "uv" ]; then
        uv run pytest --cov=. --cov-report=html --cov-report=term -q
    else
        pytest --cov=. --cov-report=html --cov-report=term -q
    fi
    echo -e "${GREEN}✓ 覆盖率报告已生成${NC}"
    echo ""

    # 显示覆盖率摘要
    echo -e "${GREEN}[4/5] 覆盖率摘要:${NC}"
    if [ "$PACKAGE_MANAGER" = "uv" ]; then
        uv run pytest --cov=. --cov-report=term --no-header -q | grep -E "TOTAL|^calculation|^data|^service|^utils"
    else
        pytest --cov=. --cov-report=term --no-header -q | grep -E "TOTAL|^calculation|^data|^service|^utils"
    fi
    echo ""

    # 检查HTML报告
    echo -e "${GREEN}[5/5] 查看详细覆盖率报告:${NC}"
    echo -e "HTML报告位置: ${YELLOW}htmlcov/index.html${NC}"
    echo -e "在浏览器中打开查看详细信息"
    echo ""

    # 尝试自动打开浏览器(macOS)
    if [[ "$OSTYPE" == "darwin"* ]]; then
        read -p "是否在浏览器中打开覆盖率报告? (y/n) " -n 1 -r
        echo
        if [[ $REPLY =~ ^[Yy]$ ]]; then
            open htmlcov/index.html
        fi
    fi
else
    echo -e "${RED}✗ 测试失败${NC}"
    echo ""
    echo -e "${YELLOW}提示: 运行以下命令查看详细错误信息:${NC}"
    echo -e "pytest -v -s"
    exit $TEST_EXIT_CODE
fi

echo ""
echo -e "${GREEN}======================================${NC}"
echo -e "${GREEN}测试完成!${NC}"
echo -e "${GREEN}======================================${NC}"
