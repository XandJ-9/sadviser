/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}", // 匹配 src 目录下所有相关文件
  ],
  theme: {
    extend: {
      colors: {
        primary: '#2563EB',    // 主色：专业蓝，适配数据系统
        secondary: '#4B5563',  // 辅助色：中性灰，用于次要文本/边框
        success: '#10B981',    // 成功色：绿色，用于确认/已选状态
        warning: '#F59E0B',    // 警告色：黄色，用于待配置/提醒
        danger: '#EF4444',     // 危险色：红色，用于错误/删除
        light: '#F9FAFB',      // 浅色背景：用于卡片/面板
        'light-border': '#E5E7EB' // 浅色边框：用于分隔元素
      },
      fontFamily: {
        inter: ['Inter', 'system-ui', 'sans-serif'],
      },
    },
  },
  plugins: [],
}
