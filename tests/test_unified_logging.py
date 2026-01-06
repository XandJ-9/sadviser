"""
测试统一日志格式
"""
import sys
import logging

sys.path.insert(0, '/Users/xujia/MyCode/sadviser')

from utils.custom_logger import CustomLogger


def test_all_log_levels():
    """测试所有日志级别"""
    print("\n" + "=" * 70)
    print("测试 1: 所有日志级别")
    print("=" * 70 + "\n")

    logger = CustomLogger(name="TestModule", log_level=logging.DEBUG)

    logger.debug("调试信息：正在初始化模块")
    logger.info("普通信息：模块加载完成")
    logger.warning("警告信息：配置文件使用了默认值")
    logger.error("错误信息：无法连接到数据库")
    logger.critical("严重错误：系统内存不足")

    print()


def test_different_modules():
    """测试不同模块的日志"""
    print("\n" + "=" * 70)
    print("测试 2: 不同模块的日志")
    print("=" * 70 + "\n")

    # 创建不同层级的日志器
    api_logger = CustomLogger(name="stock_api")
    service_logger = CustomLogger(name="StockService")
    repo_logger = CustomLogger(name="StockRepository")
    container_logger = CustomLogger(name="Container")

    api_logger.info("处理请求: GET /api/v1/stocks/")
    service_logger.info("获取股票列表: limit=50, offset=0")
    repo_logger.info("查询数据库: SELECT * FROM stock_list LIMIT 50")
    container_logger.info("创建 PostgreSQL 存储实例")

    print()


def test_colored_output():
    """测试彩色输出"""
    print("\n" + "=" * 70)
    print("测试 3: 彩色输出")
    print("=" * 70 + "\n")

    logger = CustomLogger(name="ColorTest")

    logger.debug("这是青色的 DEBUG 日志")
    logger.info("这是绿色的 INFO 日志")
    logger.warning("这是黄色的 WARNING 日志")
    logger.error("这是红色的 ERROR 日志")
    logger.critical("这是红底白色的 CRITICAL 日志")

    print()


def test_real_world_scenario():
    """测试真实场景"""
    print("\n" + "=" * 70)
    print("测试 4: 真实场景模拟")
    print("=" * 70 + "\n")

    # 模拟 API 请求处理
    api_logger = CustomLogger(name="stock_api")
    service_logger = CustomLogger(name="StockService")
    repo_logger = CustomLogger(name="StockRepository")

    api_logger.info("收到请求: GET /api/v1/stocks/000001")
    service_logger.info("获取股票详情: symbol=000001")
    repo_logger.info("查询数据库: stock_list WHERE symbol='000001'")

    try:
        # 模拟错误
        repo_logger.error("数据库查询失败: connection timeout")
        service_logger.error("获取股票详情失败: 000001, error=Database error")
        api_logger.error("请求处理失败: Internal server error")
    except Exception as e:
        logger.error(f"异常: {e}")

    print()


def test_module_name_formatting():
    """测试模块名格式化"""
    print("\n" + "=" * 70)
    print("测试 5: 模块名格式化")
    print("=" * 70 + "\n")

    # 测试带点号的模块名
    logger1 = CustomLogger(name="service.api.v1.stock_api")
    logger2 = CustomLogger(name="StockService")
    logger3 = CustomLogger(name="data.storage.postgres_storage")

    logger1.info("完整路径模块名")
    logger2.info("简单模块名")
    logger3.info("数据层模块名")

    print()


def test_performance_logging():
    """测试性能日志"""
    print("\n" + "=" * 70)
    print("测试 6: 性能相关日志")
    print("=" * 70 + "\n")

    logger = CustomLogger(name="Performance")

    import time
    start = time.time()
    logger.info("开始批量处理股票数据")

    # 模拟处理
    time.sleep(0.01)

    duration = (time.time() - start) * 1000
    logger.info(f"批量处理完成: 处理了 {100} 只股票, 耗时 {duration:.2f}ms")

    print()


if __name__ == "__main__":
    test_all_log_levels()
    test_different_modules()
    test_colored_output()
    test_real_world_scenario()
    test_module_name_formatting()
    test_performance_logging()

    print("\n" + "=" * 70)
    print("✅ 所有日志测试完成！")
    print("=" * 70 + "\n")
