"""
统一日志系统 - 支持控制台和文件的统一格式
"""
import logging
import os
import sys
from datetime import datetime
from typing import Optional, Dict, List, Union
import colorama

colorama.init(autoreset=True)


class CustomFormatter(logging.Formatter):
    """
    自定义日志格式化器

    控制台格式：简洁、颜色化、易读
    文件格式：详细、包含所有调试信息
    """

    # 日志级别颜色映射
    LEVEL_COLORS = {
        logging.DEBUG: colorama.Fore.CYAN,
        logging.INFO: colorama.Fore.GREEN,
        logging.WARNING: colorama.Fore.YELLOW,
        logging.ERROR: colorama.Fore.RED,
        logging.CRITICAL: colorama.Back.RED + colorama.Fore.WHITE
    }

    # 日志级别简短标识
    LEVEL_NAMES = {
        logging.DEBUG: "DEBUG",
        logging.INFO: "INFO ",
        logging.WARNING: "WARN ",
        logging.ERROR: "ERROR",
        logging.CRITICAL: "CRIT "
    }

    def __init__(self, use_color: bool = True, console_mode: bool = True):
        """
        初始化格式化器

        Args:
            use_color: 是否使用颜色
            console_mode: 是否为控制台模式（控制台格式简洁，文件格式详细）
        """
        self.use_color = use_color and console_mode
        self.console_mode = console_mode
        super().__init__()

    def format(self, record: logging.LogRecord) -> str:
        if self.console_mode:
            return self._format_console(record)
        else:
            return self._format_file(record)

    def _format_console(self, record: logging.LogRecord) -> str:
        """
        格式化控制台日志 - 简洁、易读

        格式: HH:MM:SS [LEVEL] ModuleName - Message
        示例: 22:30:45 [INFO] StockService - 获取股票列表成功
        """
        # 时间戳（只显示时分秒）
        timestamp = datetime.fromtimestamp(record.created).strftime("%H:%M:%S")

        # 日志级别
        level_name = self.LEVEL_NAMES.get(record.levelno, record.levelname)

        # 模块名（只显示最后部分）
        module_name = record.name.split('.')[-1] if '.' in record.name else record.name

        # 消息
        message = record.getMessage()

        # 构建格式字符串
        log_str = f"{timestamp} [{level_name}] {module_name} - {message}"

        # 添加颜色
        if self.use_color and record.levelno in self.LEVEL_COLORS:
            color = self.LEVEL_COLORS[record.levelno]
            log_str = color + log_str + colorama.Style.RESET_ALL

        return log_str

    def _format_file(self, record: logging.LogRecord) -> str:
        """
        格式化文件日志 - 详细、包含调试信息

        格式: YYYY-MM-DD HH:MM:SS - LEVEL - module.py:line - function() - Message
        示例: 2025-01-06 22:30:45 - INFO - stock_service.py:123 - get_stock_list() - 获取股票列表成功
        """
        timestamp = self.formatTime(record, "%Y-%m-%d %H:%M:%S")
        level_name = record.levelname
        filename = os.path.basename(record.pathname)
        lineno = record.lineno
        func_name = record.funcName
        message = record.getMessage()

        return f"{timestamp} - {level_name:5} - {filename}:{lineno} - {func_name}() - {message}"


class CustomLogger(logging.Logger):
    """
    自定义日志类

    特点：
    1. 统一的控制台格式（简洁、颜色化）
    2. 详细的文件格式（包含完整调试信息）
    3. 自动处理日志目录
    4. 支持按级别分离日志文件
    """

    def __init__(
        self,
        name: str,
        log_level: Union[int, str] = logging.INFO,
        log_dir: Optional[str] = None,
        file_name: Optional[str] = None,
        separate_levels: bool = False,
        enable_console: bool = True,
        enable_file: bool = True
    ):
        """
        初始化自定义日志器

        Args:
            name: 日志器名称
            log_level: 日志级别，默认为 INFO
            log_dir: 日志文件存储目录，None 表示不保存到文件
            file_name: 日志文件名，不指定则自动生成
            separate_levels: 是否按级别分离日志文件
            enable_console: 是否在控制台输出日志
            enable_file: 是否输出到文件
        """
        super().__init__(name, log_level)

        self.log_dir = log_dir
        self.separate_levels = separate_levels
        self.enable_console = enable_console
        self.enable_file = enable_file

        # 确保日志目录存在
        self._ensure_log_dir_exists()

        # 生成日志文件名
        self.base_file_name = file_name or self._generate_default_filename()

        # 配置处理器
        self._configure_handlers()

    def _ensure_log_dir_exists(self) -> None:
        """确保日志目录存在"""
        if self.log_dir and not os.path.exists(self.log_dir):
            os.makedirs(self.log_dir, exist_ok=True)

    def _generate_default_filename(self) -> str:
        """生成默认的日志文件名"""
        timestamp = datetime.now().strftime("%Y%m%d")
        return f"{timestamp}_{self.name}"

    def _configure_handlers(self) -> None:
        """配置日志处理器"""
        # 清除已有处理器
        if self.handlers:
            self.handlers.clear()

        # 配置控制台处理器
        if self.enable_console:
            console_handler = logging.StreamHandler(sys.stdout)
            console_handler.setFormatter(CustomFormatter(use_color=True, console_mode=True))
            console_handler.setLevel(self.level)
            self.addHandler(console_handler)

        # 如果不需要文件日志，直接返回
        if not self.enable_file or self.log_dir is None:
            return

        # 配置文件处理器
        if self.separate_levels:
            # 按级别分离日志文件
            levels = [
                (logging.DEBUG, "debug"),
                (logging.INFO, "info"),
                (logging.WARNING, "warning"),
                (logging.ERROR, "error"),
                (logging.CRITICAL, "critical")
            ]

            for level, level_name in levels:
                file_handler = logging.FileHandler(
                    os.path.join(self.log_dir, f"{self.base_file_name}_{level_name}.log")
                )
                file_handler.setFormatter(CustomFormatter(use_color=False, console_mode=False))
                file_handler.setLevel(level)

                # 添加过滤器，只保留当前级别的日志
                class LevelFilter(logging.Filter):
                    def __init__(self, level):
                        self.level = level

                    def filter(self, record):
                        return record.levelno == self.level

                file_handler.addFilter(LevelFilter(level))
                self.addHandler(file_handler)
        else:
            # 所有级别日志输出到同一个文件
            file_handler = logging.FileHandler(
                os.path.join(self.log_dir, f"{self.base_file_name}.log")
            )
            file_handler.setFormatter(CustomFormatter(use_color=False, console_mode=False))
            file_handler.setLevel(self.level)
            self.addHandler(file_handler)

    def set_log_level(self, level: Union[int, str]) -> None:
        """设置日志级别"""
        self.setLevel(level)
        for handler in self.handlers:
            handler.setLevel(level)

    def get_log_file_paths(self) -> Dict[str, str]:
        """获取所有日志文件的路径"""
        log_files = {}
        for handler in self.handlers:
            if isinstance(handler, logging.FileHandler):
                if self.separate_levels:
                    for level, level_name in [
                        (logging.DEBUG, "debug"),
                        (logging.INFO, "info"),
                        (logging.WARNING, "warning"),
                        (logging.ERROR, "error"),
                        (logging.CRITICAL, "critical")
                    ]:
                        if f"_{level_name}.log" in handler.baseFilename:
                            log_files[level_name.upper()] = handler.baseFilename
                            break
                else:
                    log_files["ALL"] = handler.baseFilename
        return log_files


# 使用示例和测试
def demo_logging():
    """演示统一日志格式"""
    print("\n" + "=" * 60)
    print("统一日志格式演示")
    print("=" * 60 + "\n")

    # 创建日志器
    logger = CustomLogger(
        name="DemoModule",
        log_level=logging.DEBUG,
        enable_console=True,
        enable_file=False
    )

    # 演示各级别日志
    logger.debug("这是一条调试信息")
    logger.info("这是一条普通信息")
    logger.warning("这是一条警告信息")
    logger.error("这是一条错误信息")
    logger.critical("这是一条严重错误信息")

    print("\n" + "=" * 60)
    print("不同模块演示")
    print("=" * 60 + "\n")

    # 创建不同模块的日志器
    stock_logger = CustomLogger(name="StockService", log_level=logging.INFO)
    repo_logger = CustomLogger(name="StockRepository", log_level=logging.INFO)
    api_logger = CustomLogger(name="StockAPI", log_level=logging.INFO)

    stock_logger.info("获取股票列表: limit=50")
    repo_logger.info("查询数据库: SELECT * FROM stock_list")
    api_logger.info("处理请求: GET /api/v1/stocks")

    print("\n" + "=" * 60)
    print("带参数的日志演示")
    print("=" * 60 + "\n")

    stock_logger.info(f"获取股票详情: symbol={'000001'}")
    repo_logger.error(f"数据库连接失败: {RuntimeError('Connection timeout')}")
    api_logger.warning(f"请求参数无效: limit={-1}")

    print()


if __name__ == "__main__":
    demo_logging()
