# 前端样式统一化文档

## 概述

本文档描述了 sadviser 前端的统一设计系统，基于 Tailwind CSS v4 构建，确保所有页面和组件具有一致的视觉风格和用户体验。

## 设计原则

1. **一致性**: 所有页面使用统一的颜色、间距、字体和组件
2. **响应式**: 优先移动端设计，使用 Tailwind 响应式工具类
3. **可访问性**: 确保足够的颜色对比度和交互反馈
4. **性能**: 使用 Tailwind 的 JIT 模式，减少 CSS 体积

## 颜色系统

### 主色调
- **Primary Blue**: `blue-600` (#2563EB) - 主要操作、链接、强调
- **Gray Scale**:
  - `gray-50`: 背景色
  - `gray-100` - `gray-900`: 文本和边框
  - `gray-200`: 次要背景
  - `gray-600`: 次要文本
  - `gray-900`: 主要文本

### 语义颜色
- **Success**: `green-600` - 上涨、成功、积极状态
- **Danger**: `red-600` - 下跌、错误、消极状态
- **Warning**: `yellow-500` - 警告、待处理
- **Info**: `cyan-500` - 信息提示

### 股票特定颜色
- **上涨**: `red-600` (中国股市红色代表上涨)
- **下跌**: `green-600` (中国股市绿色代表下跌)

## 排版

### 字体大小
```jsx
// 标题
text-3xl        // 30px - 页面主标题
text-xl         // 20px - 卡片标题
text-lg         // 18px - 子标题

// 正文
text-base       // 16px - 默认正文
text-sm         // 14px - 次要文本
text-xs         // 12px - 辅助文本
```

### 字重
```jsx
font-bold       // 700 - 标题、强调
font-semibold   // 600 - 次级标题
font-medium     // 500 - 按钮、标签
font-normal     // 400 - 正文
```

## 间距系统

使用 Tailwind 默认间距单位（4px 基准）：

```jsx
p-4    // 16px - 内边距
p-6    // 24px - 卡片内边距
px-6   // 水平 24px
py-4   // 垂直 16px

gap-4  // 16px - 元素间距
gap-6  // 24px - 卡片间距

mb-4   // 下边距 16px
mb-8   // 下边距 32px
```

## 布局

### 容器
```jsx
<div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
  {/* 内容 */}
</div>
```

### 网格系统
```jsx
// 响应式网格
<div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-6">
  {/* 子元素 */}
</div>
```

### 卡片布局
```jsx
<div className="bg-white rounded-lg border border-gray-200 shadow-sm">
  <div className="px-6 py-4 border-b border-gray-200">
    {/* 卡片头部 */}
  </div>
  <div className="px-6 py-4">
    {/* 卡片内容 */}
  </div>
</div>
```

## 组件库

### 可复用 UI 组件

位置: `frontend/src/components/ui/`

#### Button 组件
```jsx
import { Button } from '../components/ui';

<Button variant="primary" size="md" onClick={handleClick}>
  点击按钮
</Button>
```

变体:
- `primary` - 主要按钮
- `secondary` - 次要按钮
- `success` - 成功按钮
- `danger` - 危险按钮
- `outline` - 轮廓按钮
- `ghost` - 幽灵按钮

#### Card 组件
```jsx
import { Card } from '../components/ui';

<Card
  title="卡片标题"
  subtitle="副标题"
  extra={<button>操作</button>}
>
  {/* 内容 */}
</Card>
```

#### StatCard 组件
```jsx
import { StatCard } from '../components/ui';

<StatCard
  title="总成交量"
  value="1.2亿"
  icon="📊"
  variant="primary"
  change="+12%"
  changeType="positive"
  trend="较昨日"
/>
```

变体:
- `default` - 默认白色卡片
- `primary` - 蓝色渐变卡片
- `success` - 绿色渐变卡片
- `danger` - 红色渐变卡片
- `warning` - 黄橙色渐变卡片
- `info` - 青蓝色渐变卡片

#### Badge 组件
```jsx
import { Badge } from '../components/ui';

<Badge variant="success" size="md">
  活跃
</Badge>
```

#### Loading 组件
```jsx
import { Loading } from '../components/ui';

<Loading size="md" text="加载中..." fullScreen={false} />
```

## 页面模板

### 标准页面结构
```jsx
function MyPage() {
  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
      {/* 页面头部 */}
      <div className="mb-8">
        <h1 className="text-3xl font-bold text-gray-900">页面标题</h1>
        <p className="mt-2 text-gray-600">页面描述</p>
      </div>

      {/* 主要内容 */}
      <div className="bg-white rounded-lg border border-gray-200 shadow-sm">
        {/* ... */}
      </div>
    </div>
  );
}
```

### 卡片列表页面
```jsx
<div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-6">
  {items.map(item => (
    <Card key={item.id}>
      {/* 卡片内容 */}
    </Card>
  ))}
</div>
```

### 数据表格页面
```jsx
<div className="bg-white rounded-lg border border-gray-200 shadow-sm">
  <div className="px-6 py-4 border-b border-gray-200">
    <h2 className="text-xl font-semibold text-gray-900">数据列表</h2>
  </div>
  <div className="overflow-x-auto">
    <table className="min-w-full divide-y divide-gray-200">
      {/* 表格内容 */}
    </table>
  </div>
</div>
```

## 常见模式

### 加载状态
```jsx
{loading ? (
  <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
    {[1, 2, 3, 4, 5, 6].map((i) => (
      <div key={i} className="h-32 bg-gray-200 rounded-lg animate-pulse"></div>
    ))}
  </div>
) : (
  {/* 实际内容 */}
)}
```

### 错误状态
```jsx
{error && (
  <div className="bg-red-50 border border-red-200 rounded-lg p-6">
    <p className="text-red-800 mb-4">{error}</p>
    <button
      onClick={handleRetry}
      className="px-4 py-2 bg-red-600 text-white rounded-lg hover:bg-red-700 transition-colors"
    >
      重试
    </button>
  </div>
)}
```

### 空状态
```jsx
{items.length === 0 && (
  <div className="px-6 py-12 text-center">
    <p className="text-gray-500">暂无数据</p>
  </div>
)}
```

## 动画和过渡

### 标准过渡
```jsx
className="transition-all duration-200"
className="hover:bg-gray-50 transition-colors"
```

### 悬停效果
```jsx
// 卡片悬停
className="hover:shadow-lg hover:-translate-y-1 transition-all duration-200"

// 按钮悬停
className="hover:bg-blue-700 transition-colors"
```

## 表单样式

### 输入框
```jsx
<input
  type="text"
  className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 transition-all"
  placeholder="请输入..."
/>
```

### 选择框
```jsx
<select className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 transition-all">
  <option>选项1</option>
  <option>选项2</option>
</select>
```

## 迁移指南

### 从旧 CSS 迁移到 Tailwind

**之前 (CSS 文件):**
```jsx
// styles/MyPage.css
.page { max-width: 1400px; margin: 0 auto; padding: 0 20px; }
.title { font-size: 32px; font-weight: 700; color: #111827; }
```

**之后 (Tailwind):**
```jsx
<div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
  <h1 className="text-3xl font-bold text-gray-900">标题</h1>
</div>
```

### 组件迁移步骤

1. 移除 CSS 导入
2. 用 Tailwind 类替换样式
3. 使用统一的 UI 组件
4. 确保响应式设计
5. 测试所有交互状态

## 最佳实践

1. **优先使用组件库**: 使用 `components/ui/` 中的可复用组件
2. **保持一致性**: 复制粘贴模式，不要重复造轮子
3. **响应式优先**: 始终考虑移动端体验
4. **语义化类名**: 使用 Tailwind 的语义化颜色和间距
5. **性能优化**: 避免内联样式，使用 Tailwind 类

## 浏览器兼容性

- Chrome/Edge: 最新 2 个版本
- Firefox: 最新 2 个版本
- Safari: 最新 2 个版本
- 移动浏览器: iOS Safari 12+, Chrome Android

## 资源链接

- [Tailwind CSS 文档](https://tailwindcss.com/docs)
- [Tailwind v4 更新](https://tailwindcss.com/blog/tailwindcss-v4-alpha)
- 组件位置: `frontend/src/components/ui/`
- 示例页面: `frontend/src/pages/HomePage.jsx`
