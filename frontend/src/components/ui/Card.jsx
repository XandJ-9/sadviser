/**
 * 统一的卡片组件
 */
const Card = ({
  children,
  title,
  subtitle,
  extra,
  className = '',
  bodyClassName = '',
  noPadding = false,
  hover = false
}) => {
  return (
    <div className={`bg-white rounded-lg border border-gray-200 ${hover ? 'hover:shadow-lg hover:-translate-y-1 transition-all duration-200' : ''} ${className}`}>
      {(title || subtitle || extra) && (
        <div className="px-6 py-4 border-b border-gray-200">
          <div className="flex items-center justify-between">
            <div>
              {title && <h3 className="text-lg font-semibold text-gray-900">{title}</h3>}
              {subtitle && <p className="mt-1 text-sm text-gray-500">{subtitle}</p>}
            </div>
            {extra && <div>{extra}</div>}
          </div>
        </div>
      )}
      <div className={noPadding ? '' : 'px-6 py-4'}>
        {children}
      </div>
    </div>
  );
};

export default Card;
