const StatCard = ({ title, value, subtitle, icon: Icon, trend }) => {
  return (
    <div className="card">
      <div className="flex items-start justify-between">
        <div className="flex-1">
          <p className="text-sm font-medium text-gray-600">{title}</p>
          <p className="mt-2 text-3xl font-bold text-gray-900">{value}</p>
          {subtitle && (
            <p className="mt-1 text-sm text-gray-500">{subtitle}</p>
          )}
        </div>
        {Icon && (
          <div className="rounded-lg bg-primary-50 p-3">
            <Icon className="h-6 w-6 text-primary-600" />
          </div>
        )}
      </div>
      {trend && (
        <div className="mt-4">
          <span
            className={`text-sm font-medium ${
              trend.isPositive ? 'text-green-600' : 'text-red-600'
            }`}
          >
            {trend.value}
          </span>
          <span className="ml-2 text-sm text-gray-500">{trend.label || 'vs last period'}</span>
        </div>
      )}
    </div>
  )
}

export default StatCard
