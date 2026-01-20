/**
 * 统一的统计卡片组件
 */
const StatCard = ({
  title,
  value,
  change,
  changeType = 'neutral',
  icon,
  variant = 'default',
  trend,
  className = ''
}) => {
  const variantStyles = {
    default: 'bg-white border-gray-200',
    primary: 'bg-gradient-to-br from-blue-500 to-blue-600 text-white',
    success: 'bg-gradient-to-br from-green-500 to-green-600 text-white',
    warning: 'bg-gradient-to-br from-yellow-500 to-orange-500 text-white',
    danger: 'bg-gradient-to-br from-red-500 to-red-600 text-white',
    info: 'bg-gradient-to-br from-cyan-500 to-blue-500 text-white'
  };

  const changeColorStyles = {
    positive: 'text-green-600',
    negative: 'text-red-600',
    neutral: 'text-gray-600'
  };

  const isColored = variant !== 'default';

  return (
    <div className={`rounded-lg border p-6 transition-all duration-200 hover:shadow-lg ${variantStyles[variant]} ${className}`}>
      <div className="flex items-center justify-between">
        <div className="flex-1">
          <p className={`text-sm font-medium ${isColored ? 'text-white/80' : 'text-gray-600'}`}>
            {title}
          </p>
          <p className={`mt-2 text-3xl font-bold ${isColored ? 'text-white' : 'text-gray-900'}`}>
            {value}
          </p>
          {(change || trend) && (
            <div className="mt-2 flex items-center gap-2">
              {change && (
                <span className={`text-sm font-medium ${changeColorStyles[changeType]}`}>
                  {changeType === 'positive' && '↑'}
                  {changeType === 'negative' && '↓'}
                  {change}
                </span>
              )}
              {trend && (
                <p className={`text-xs ${isColored ? 'text-white/70' : 'text-gray-500'}`}>
                  {trend}
                </p>
              )}
            </div>
          )}
        </div>
        {icon && (
          <div className={`ml-4 flex h-12 w-12 flex-shrink-0 items-center justify-center rounded-lg ${isColored ? 'bg-white/20' : 'bg-gray-100'}`}>
            <span className="text-2xl">{icon}</span>
          </div>
        )}
      </div>
    </div>
  );
};

export default StatCard;
