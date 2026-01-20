-- 创建股票数据表

-- 股票日线数据表
CREATE TABLE IF NOT EXISTS stock_daily_data (
    id SERIAL PRIMARY KEY,
    symbol VARCHAR(20) NOT NULL,
    date DATE NOT NULL,
    open DECIMAL(10, 2) NOT NULL,
    high DECIMAL(10, 2) NOT NULL,
    low DECIMAL(10, 2) NOT NULL,
    close DECIMAL(10, 2) NOT NULL,
    volume BIGINT NOT NULL,
    amount DECIMAL(20, 2) NOT NULL,
    source VARCHAR(50) NOT NULL DEFAULT 'akshare',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(symbol, date, source)
);

-- 创建索引
CREATE INDEX IF NOT EXISTS idx_stock_daily_symbol ON stock_daily_data(symbol);
CREATE INDEX IF NOT EXISTS idx_stock_daily_date ON stock_daily_data(date);
CREATE INDEX IF NOT EXISTS idx_stock_daily_symbol_date ON stock_daily_data(symbol, date);

-- 实时行情表
CREATE TABLE IF NOT EXISTS stock_quotes (
    id SERIAL PRIMARY KEY,
    symbol VARCHAR(20) NOT NULL,
    name VARCHAR(100),
    price DECIMAL(10, 2),
    open DECIMAL(10, 2),
    high DECIMAL(10, 2),
    low DECIMAL(10, 2),
    prev_close DECIMAL(10, 2),
    volume BIGINT,
    amount DECIMAL(20, 2),
    change DECIMAL(10, 2),
    change_percent DECIMAL(10, 2),
    date DATE,
    time TIME,
    source VARCHAR(50) NOT NULL DEFAULT 'akshare',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 创建索引
CREATE INDEX IF NOT EXISTS idx_stock_quotes_symbol ON stock_quotes(symbol);
CREATE INDEX IF NOT EXISTS idx_stock_quotes_date ON stock_quotes(date);
CREATE INDEX IF NOT EXISTS idx_stock_quotes_source ON stock_quotes(source);

-- 股票列表表
CREATE TABLE IF NOT EXISTS stock_list (
    id SERIAL PRIMARY KEY,
    symbol VARCHAR(20) UNIQUE NOT NULL,
    name VARCHAR(100) NOT NULL,
    source VARCHAR(50) NOT NULL DEFAULT 'akshare',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 创建索引
CREATE INDEX IF NOT EXISTS idx_stock_list_symbol ON stock_list(symbol);
CREATE INDEX IF NOT EXISTS idx_stock_list_source ON stock_list(source);

-- 任务状态表
CREATE TABLE IF NOT EXISTS tasks (
    id VARCHAR(50) PRIMARY KEY,
    type VARCHAR(50),
    status VARCHAR(20) NOT NULL,
    message TEXT,
    progress INTEGER DEFAULT 0,
    total INTEGER DEFAULT 0,
    success INTEGER DEFAULT 0,
    failed INTEGER DEFAULT 0,
    meta JSONB,
    priority VARCHAR(20) DEFAULT 'medium',
    error TEXT,
    started_at TIMESTAMP,
    completed_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 创建索引
CREATE INDEX IF NOT EXISTS idx_tasks_status ON tasks(status);
CREATE INDEX IF NOT EXISTS idx_tasks_created_at ON tasks(created_at);

-- 添加注释
COMMENT ON TABLE stock_daily_data IS '股票日线数据';
COMMENT ON TABLE stock_quotes IS '实时行情数据';
COMMENT ON TABLE stock_list IS '股票列表';
COMMENT ON TABLE tasks IS '系统任务状态';
