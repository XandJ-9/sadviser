"""
PostgreSQL存储模块测试
"""
import pytest
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import asyncio
from unittest.mock import Mock, AsyncMock, patch, MagicMock

from data.storage.postgres_storage import PostgreSQLStorage
from data.storage.base_storage import BaseStorage


@pytest.mark.asyncio
class TestPostgreSQLStorage:
    """PostgreSQL存储测试类"""

    async def test_init(self, mock_storage_config):
        """测试初始化"""
        storage = PostgreSQLStorage(**mock_storage_config)

        assert storage.config['host'] == mock_storage_config['host']
        assert storage.config['port'] == mock_storage_config['port']
        assert storage.config['database'] == mock_storage_config['database']

    async def test_connect(self, mock_storage_config):
        """测试连接数据库"""
        storage = PostgreSQLStorage(**mock_storage_config)

        # Mock asyncpg connection
        with patch('asyncpg.create_pool', new_callable=AsyncMock) as mock_pool:
            mock_conn = AsyncMock()
            mock_pool.return_value.__aenter__.return_value = mock_conn

            await storage.connect()

            assert storage._pool is not None
            mock_pool.assert_called_once()

    async def test_insert_stock_info(self, mock_storage_config):
        """测试插入股票基本信息"""
        storage = PostgreSQLStorage(**mock_storage_config)

        # Mock connection
        mock_pool = AsyncMock()
        mock_conn = AsyncMock()
        storage._pool = mock_pool

        # 测试数据
        stock_data = {
            'symbol': 'sh600000',
            'name': '浦发银行',
            'industry': '银行',
            'market': 'sh'
        }

        with patch.object(storage, '_execute_query', new_callable=AsyncMock) as mock_execute:
            mock_execute.return_value = None

            result = await storage.insert('stock_info', stock_data)

            assert result is True
            mock_execute.assert_called_once()

    async def test_insert_stock_daily_data(self, mock_storage_config, sample_ohlcv_data):
        """测试插入日线数据"""
        storage = PostgreSQLStorage(**mock_storage_config)
        storage._pool = AsyncMock()

        # 准备测试数据
        test_data = sample_ohlcv_data.iloc[0].to_dict()
        test_data['symbol'] = 'sh600000'
        test_data['date'] = test_data.name.strftime('%Y-%m-%d')

        with patch.object(storage, '_execute_query', new_callable=AsyncMock) as mock_execute:
            mock_execute.return_value = None

            result = await storage.insert('stock_daily', test_data)

            assert result is True
            mock_execute.assert_called_once()

    async def test_batch_insert(self, mock_storage_config, sample_ohlcv_data):
        """测试批量插入"""
        storage = PostgreSQLStorage(**mock_storage_config)
        storage._pool = AsyncMock()

        # 准备批量数据
        batch_data = []
        for idx, row in sample_ohlcv_data.head(10).iterrows():
            data = row.to_dict()
            data['symbol'] = 'sh600000'
            data['date'] = idx.strftime('%Y-%m-%d')
            batch_data.append(data)

        with patch.object(storage, '_execute_batch', new_callable=AsyncMock) as mock_batch:
            mock_batch.return_value = None

            result = await storage.batch_insert('stock_daily', batch_data)

            assert result is True
            mock_batch.assert_called_once()

    async def test_query_by_symbol(self, mock_storage_config):
        """测试按股票代码查询"""
        storage = PostgreSQLStorage(**mock_storage_config)
        storage._pool = AsyncMock()

        # Mock查询结果
        mock_result = [
            {'symbol': 'sh600000', 'name': '浦发银行', 'industry': '银行'},
        ]

        with patch.object(storage, '_execute_query', new_callable=AsyncMock) as mock_query:
            mock_query.return_value = mock_result

            result = await storage.query(
                'stock_info',
                conditions={'symbol': 'sh600000'}
            )

            assert len(result) == 1
            assert result[0]['symbol'] == 'sh600000'

    async def test_query_by_date_range(self, mock_storage_config):
        """测试按日期范围查询"""
        storage = PostgreSQLStorage(**mock_storage_config)
        storage._pool = AsyncMock()

        # Mock查询结果
        mock_result = [
            {
                'symbol': 'sh600000',
                'date': '2024-01-01',
                'open': 100.0,
                'high': 102.0,
                'low': 99.0,
                'close': 101.0,
                'volume': 5000000
            },
        ]

        with patch.object(storage, '_execute_query', new_callable=AsyncMock) as mock_query:
            mock_query.return_value = mock_result

            result = await storage.query(
                'stock_daily',
                conditions={
                    'symbol': 'sh600000',
                    'start_date': '2024-01-01',
                    'end_date': '2024-01-31'
                }
            )

            assert len(result) == 1
            assert result[0]['symbol'] == 'sh600000'

    async def test_query_dataframe(self, mock_storage_config):
        """测试查询返回DataFrame"""
        storage = PostgreSQLStorage(**mock_storage_config)
        storage._pool = AsyncMock()

        # Mock查询结果
        mock_records = [
            {
                'symbol': 'sh600000',
                'date': '2024-01-01',
                'open': 100.0,
                'high': 102.0,
                'low': 99.0,
                'close': 101.0,
                'volume': 5000000
            },
            {
                'symbol': 'sh600000',
                'date': '2024-01-02',
                'open': 101.0,
                'high': 103.0,
                'low': 100.0,
                'close': 102.0,
                'volume': 6000000
            },
        ]

        with patch.object(storage, '_execute_query', new_callable=AsyncMock) as mock_query:
            mock_query.return_value = mock_records

            result = await storage.query_dataframe(
                'stock_daily',
                conditions={'symbol': 'sh600000'}
            )

            assert isinstance(result, pd.DataFrame)
            assert len(result) == 2
            assert 'symbol' in result.columns
            assert 'close' in result.columns

    async def test_update(self, mock_storage_config):
        """测试更新数据"""
        storage = PostgreSQLStorage(**mock_storage_config)
        storage._pool = AsyncMock()

        update_data = {
            'name': '浦发银行股份有限公司',
            'industry': '银行业'
        }

        with patch.object(storage, '_execute_query', new_callable=AsyncMock) as mock_execute:
            mock_execute.return_value = None

            result = await storage.update(
                'stock_info',
                data=update_data,
                conditions={'symbol': 'sh600000'}
            )

            assert result is True
            mock_execute.assert_called_once()

    async def test_delete(self, mock_storage_config):
        """测试删除数据"""
        storage = PostgreSQLStorage(**mock_storage_config)
        storage._pool = AsyncMock()

        with patch.object(storage, '_execute_query', new_callable=AsyncMock) as mock_execute:
            mock_execute.return_value = None

            result = await storage.delete(
                'stock_daily',
                conditions={'symbol': 'sh600000'}
            )

            assert result is True
            mock_execute.assert_called_once()

    async def test_table_exists(self, mock_storage_config):
        """测试检查表是否存在"""
        storage = PostgreSQLStorage(**mock_storage_config)
        storage._pool = AsyncMock()

        with patch.object(storage, '_execute_query', new_callable=AsyncMock) as mock_query:
            # 表存在
            mock_query.return_value = [{'exists': True}]
            result = await storage.table_exists('stock_info')
            assert result is True

            # 表不存在
            mock_query.return_value = [{'exists': False}]
            result = await storage.table_exists('stock_info')
            assert result is False

    async def test_create_table(self, mock_storage_config):
        """测试创建表"""
        storage = PostgreSQLStorage(**mock_storage_config)
        storage._pool = AsyncMock()

        with patch.object(storage, '_execute_query', new_callable=AsyncMock) as mock_execute:
            mock_execute.return_value = None

            result = await storage.create_table('stock_info')

            assert result is True
            mock_execute.assert_called()

    async def test_add_timestamps(self, mock_storage_config):
        """测试自动添加时间戳"""
        storage = PostgreSQLStorage(**mock_storage_config)

        test_data = {
            'symbol': 'sh600000',
            'name': '浦发银行'
        }

        result = storage._add_timestamps(test_data, 'insert')

        assert 'created_at' in result
        assert 'updated_at' in result
        assert isinstance(result['created_at'], datetime)

    async def test_close(self, mock_storage_config):
        """测试关闭连接"""
        storage = PostgreSQLStorage(**mock_storage_config)

        # Mock pool
        mock_pool = AsyncMock()
        storage._pool = mock_pool

        await storage.close()

        mock_pool.close.assert_called_once()


@pytest.mark.asyncio
class TestPostgreSQLStorageErrorHandling:
    """错误处理测试"""

    async def test_connection_failure(self, mock_storage_config):
        """测试连接失败处理"""
        storage = PostgreSQLStorage(**mock_storage_config)

        with patch('asyncpg.create_pool', side_effect=Exception('Connection failed')):
            with pytest.raises(Exception):
                await storage.connect()

    async def test_insert_without_connection(self, mock_storage_config):
        """测试未连接时插入数据"""
        storage = PostgreSQLStorage(**mock_storage_config)
        storage._pool = None

        with pytest.raises(Exception, match='Not connected'):
            await storage.insert('stock_info', {'symbol': 'sh600000'})

    async def test_invalid_table_name(self, mock_storage_config):
        """测试无效表名"""
        storage = PostgreSQLStorage(**mock_storage_config)
        storage._pool = AsyncMock()

        with patch.object(storage, '_execute_query', side_effect=Exception('Table not found')):
            with pytest.raises(Exception):
                await storage.query('invalid_table')


@pytest.mark.asyncio
class TestPostgreSQLStoragePerformance:
    """性能测试"""

    async def test_large_batch_insert(self, mock_storage_config):
        """测试大批量插入性能"""
        storage = PostgreSQLStorage(**mock_storage_config)
        storage._pool = AsyncMock()

        # 生成1000条数据
        large_data = []
        for i in range(1000):
            large_data.append({
                'symbol': f'sh60000{i % 10}',
                'name': f'股票{i}'
            })

        with patch.object(storage, '_execute_batch', new_callable=AsyncMock) as mock_batch:
            mock_batch.return_value = None

            import time
            start_time = time.time()

            result = await storage.batch_insert('stock_info', large_data)

            elapsed_time = time.time() - start_time

            assert result is True
            # 批量插入应该在合理时间内完成(例如<1秒)
            assert elapsed_time < 1.0

    async def test_query_performance(self, mock_storage_config):
        """测试查询性能"""
        storage = PostgreSQLStorage(**mock_storage_config)
        storage._pool = AsyncMock()

        # Mock返回大量数据
        large_result = [
            {'symbol': f'sh60000{i}', 'name': f'股票{i}'}
            for i in range(1000)
        ]

        with patch.object(storage, '_execute_query', new_callable=AsyncMock) as mock_query:
            mock_query.return_value = large_result

            import time
            start_time = time.time()

            result = await storage.query('stock_info')

            elapsed_time = time.time() - start_time

            assert len(result) == 1000
            # 查询应该在合理时间内完成
            assert elapsed_time < 0.5
