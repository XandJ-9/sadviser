import logging
import os
import sys
from datetime import datetime
from typing import Optional, Dict, List, Union
import colorama

colorama.init(autoreset=True)


class CustomLogger(logging.Logger):
    """
    自定义日志类，继承自logging.Logger
    支持自定义输出样式、日志文件配置、不同级别日志分离等功能
    """
    
    LEVEL_COLORS = {
        logging.DEBUG: colorama.Fore.CYAN,
        logging.INFO: colorama.Fore.GREEN,
        logging.WARNING: colorama.Fore.YELLOW,
        logging.ERROR: colorama.Fore.RED,
        logging.CRITICAL: colorama.Back.RED + colorama.Fore.WHITE
    }
    def __init__(self):
      super().__init__(name=self.__class__.__name__)

    def __init__(self, 
                 name: str,
                 log_level: Union[int, str] = logging.INFO,
                 log_dir: str = None,
                 file_name: Optional[str] = None,
                 separate_levels: bool = False,
                 format_style: str = "verbose",
                 enable_console: bool = True):
        """
        初始化自定义日志器
        
        :param name: 日志器名称
        :param log_level: 日志级别，默认为INFO
        :param log_dir: 日志文件存储目录，默认 log_dir=None 表示不保存日志到文件,此配置下的日志仅输出到控制台
        :param file_name: 日志文件名，不指定则自动生成
        :param separate_levels: 是否按级别分离日志文件，True则分别生成debug、info等日志文件
        :param format_style: 日志格式样式，"simple"或"verbose"，默认为"verbose"
        :param enable_console: 是否在控制台输出日志，默认为True
        """

        if name is None:
            name = getattr(self, '__class__').__name__

        # 调用父类构造函数
        super().__init__(name, log_level)
        
        # 初始化配置参数
        self.log_dir = log_dir
        self.separate_levels = separate_levels
        self.enable_console = enable_console
        
        # 确保日志目录存在
        self._ensure_log_dir_exists()
        
        # 生成日志文件名（如果未指定）
        self.base_file_name = file_name or self._generate_default_filename()
        
        # 设置日志格式
        self.formatter = self._get_formatter(format_style)
        
        # 配置处理器
        self._configure_handlers()
    
    def _log(self, level, msg, args, exc_info = None, extra = None, stack_info = False, stacklevel = 1):
        """重写日志方法，添加颜色支持"""
        if self.enable_console and level in self.LEVEL_COLORS:
            msg = self.LEVEL_COLORS[level] + msg + colorama.Style.RESET_ALL
        return super()._log(level, msg, args, exc_info, extra, stack_info, stacklevel)

    def _ensure_log_dir_exists(self) -> None:
        """确保日志目录存在，不存在则创建"""
        if self.log_dir and not os.path.exists(self.log_dir):
            os.makedirs(self.log_dir, exist_ok=True)
    
    def _generate_default_filename(self) -> str:
        """生成默认的日志文件名，格式为"YYYYMMDD_HHMMSS_loggerName" """
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        return f"{timestamp}_{self.name}"
    
    def _get_formatter(self, format_style: str) -> logging.Formatter:
        """
        获取日志格式化器
        
        :param format_style: 格式样式，"simple"或"verbose"
        :return: 日志格式化器
        """
        if format_style == "simple":
            # 简单格式
            format_str = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
            datefmt = "%Y-%m-%d %H:%M:%S"
        else:  # verbose
            # 详细格式，包含更多信息
            format_str = (
                "%(asctime)s - %(name)s - %(levelname)s - "
                "%(filename)s:%(lineno)d - %(funcName)s() - %(message)s"
            )
            datefmt = "%Y-%m-%d %H:%M:%S"
        
        return logging.Formatter(format_str, datefmt=datefmt)
    
    def _configure_handlers(self) -> None:
        """配置日志处理器，包括文件处理器和控制台处理器"""
        # 清除已有的处理器，避免重复输出
        if self.handlers:
            self.handlers.clear()
        
        # 配置控制台处理器
        if self.enable_console:
            console_handler = logging.StreamHandler(sys.stdout)
            console_handler.setFormatter(self.formatter)
            console_handler.setLevel(self.level)
            self.addHandler(console_handler)
        
        if self.log_dir is None:
            # 如果未指定日志目录，则只使用控制台输出
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
                # 只处理指定级别及以上的日志
                file_handler = logging.FileHandler(
                    os.path.join(self.log_dir, f"{self.base_file_name}_{level_name}.log")
                )
                file_handler.setFormatter(self.formatter)
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
            file_handler.setFormatter(self.formatter)
            file_handler.setLevel(self.level)
            self.addHandler(file_handler)
    
    def set_log_level(self, level: Union[int, str]) -> None:
        """
        设置日志级别
        
        :param level: 日志级别，可以是整数或字符串，如logging.INFO或"INFO"
        """
        self.setLevel(level)
        # 更新所有处理器的级别
        for handler in self.handlers:
            handler.setLevel(level)
    
    def set_format_style(self, format_style: str) -> None:
        """
        设置日志格式样式
        
        :param format_style: 格式样式，"simple"或"verbose"
        """
        self.formatter = self._get_formatter(format_style)
        # 更新所有处理器的格式化器
        for handler in self.handlers:
            handler.setFormatter(self.formatter)
    
    def add_custom_handler(self, handler: logging.Handler) -> None:
        """
        添加自定义处理器
        
        :param handler: 日志处理器
        """
        handler.setFormatter(self.formatter)
        handler.setLevel(self.level)
        self.addHandler(handler)
    
    def get_log_file_paths(self) -> Dict[str, str]:
        """
        获取所有日志文件的路径
        
        :return: 日志级别与文件路径的字典
        """
        log_files = {}
        for handler in self.handlers:
            if isinstance(handler, logging.FileHandler):
                if self.separate_levels:
                    # 从文件名中提取级别信息
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
    
# 使用示例
def test_custom_logger():
    # 创建不同配置的日志实例
    print("创建基础日志器...")
    basic_logger = CustomLogger(
        name="basic_logger",
        log_level=logging.DEBUG,
        format_style="simple"
    )
    
    print("创建分离级别日志器...")
    separated_logger = CustomLogger(
        name="separated_logger",
        log_level=logging.INFO,
        log_dir="logs/separated_logs",
        separate_levels=True,
        format_style="verbose"
    )
    
    # 测试日志输出
    print("\n测试基础日志器输出...")
    basic_logger.debug("这是一条调试信息")
    basic_logger.info("这是一条普通信息")
    basic_logger.warning("这是一条警告信息")
    basic_logger.error("这是一条错误信息")
    basic_logger.critical("这是一条严重错误信息")
    
    print("\n测试分离级别日志器输出...")
    separated_logger.debug("这是一条调试信息")
    separated_logger.info("这是一条普通信息")
    separated_logger.warning("这是一条警告信息")
    separated_logger.error("这是一条错误信息")
    try:
        1 / 0
    except ZeroDivisionError:
        separated_logger.exception("发生了异常")  # 会自动记录堆栈信息
    separated_logger.critical("这是一条严重错误信息")
    
    # 展示日志文件路径
    print("\n基础日志器文件路径:")
    for level, path in basic_logger.get_log_file_paths().items():
        print(f"{level}: {path}")
    
    print("\n分离级别日志器文件路径:")
    for level, path in separated_logger.get_log_file_paths().items():
        print(f"{level}: {path}")
    
    # 测试动态修改日志级别
    print("\n修改基础日志器级别为WARNING...")
    basic_logger.set_log_level(logging.WARNING)
    basic_logger.info("这条信息不应该被输出")  # 不会被输出
    basic_logger.warning("这条警告信息应该被输出")  # 会被输出
    
    # 测试动态修改日志格式
    print("\n修改基础日志器格式为verbose...")
    basic_logger.set_format_style("verbose")
    basic_logger.warning("这条警告信息应该使用详细格式输出")


if __name__ == "__main__":
    test_custom_logger()
    