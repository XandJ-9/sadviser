

export const Home = () => {
  return (
    <div>
  <header className="bg-white shadow-sm sticky top-0 z-30">
    <div className="container mx-auto px-4 py-3 flex items-center justify-between">
      {/* <!-- 左侧标题区 --> */}
      <div className="flex items-center space-x-3">
        <button className="text-secondary hover:text-primary transition-colors">
          <i className="fa fa-arrow-left text-lg"></i>
        </button>
        <h1 className="text-lg font-semibold text-gray-800">多租户数据同步配置</h1>
        <span className="text-xs bg-primary/10 text-primary px-2 py-1 rounded-full">新建任务</span>
      </div>
      
      {/* <!-- 右侧操作区 --> */}
      <div className="flex items-center space-x-4">
        <button className="px-3 py-1.5 text-sm border border-light-border rounded hover:bg-light transition-colors">
          <i className="fa fa-save mr-1"></i>保存草稿
        </button>
        <button className="px-4 py-1.5 text-sm bg-primary text-white rounded hover:bg-primary/90 transition-colors">
          <i className="fa fa-check mr-1"></i>提交配置
        </button>
      </div>
    </div>
      </header>
      
    </div>
  )
}