import React from 'react'

const Dashboard: React.FC = () => {
  return (
    <div>
      <h2 className="text-2xl font-bold text-gray-900 dark:text-white mb-6">
        Dashboard
      </h2>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
        {/* Stats cards */}
        <div className="bg-white dark:bg-gray-800 p-6 rounded-lg shadow">
          <h3 className="text-sm font-medium text-gray-500 dark:text-gray-400">
            Total Users
          </h3>
          <p className="mt-2 text-3xl font-bold text-gray-900 dark:text-white">
            1,234
          </p>
          <p className="mt-2 text-sm text-green-600">
            +12% from last month
          </p>
        </div>

        <div className="bg-white dark:bg-gray-800 p-6 rounded-lg shadow">
          <h3 className="text-sm font-medium text-gray-500 dark:text-gray-400">
            Active Sessions
          </h3>
          <p className="mt-2 text-3xl font-bold text-gray-900 dark:text-white">
            987
          </p>
          <p className="mt-2 text-sm text-red-600">
            -5% from last hour
          </p>
        </div>

        <div className="bg-white dark:bg-gray-800 p-6 rounded-lg shadow">
          <h3 className="text-sm font-medium text-gray-500 dark:text-gray-400">
            Revenue
          </h3>
          <p className="mt-2 text-3xl font-bold text-gray-900 dark:text-white">
            $45,678
          </p>
          <p className="mt-2 text-sm text-green-600">
            +18% from last week
          </p>
        </div>

        <div className="bg-white dark:bg-gray-800 p-6 rounded-lg shadow">
          <h3 className="text-sm font-medium text-gray-500 dark:text-gray-400">
            Conversion Rate
          </h3>
          <p className="mt-2 text-3xl font-bold text-gray-900 dark:text-white">
            3.45%
          </p>
          <p className="mt-2 text-sm text-gray-600">
            No change
          </p>
        </div>
      </div>

      {/* Charts section placeholder */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <div className="bg-white dark:bg-gray-800 p-6 rounded-lg shadow">
          <h3 className="text-lg font-medium text-gray-900 dark:text-white mb-4">
            User Activity
          </h3>
          <div className="h-64 bg-gray-100 dark:bg-gray-700 rounded-lg flex items-center justify-center">
            <p className="text-gray-500 dark:text-gray-400">Chart placeholder</p>
          </div>
        </div>

        <div className="bg-white dark:bg-gray-800 p-6 rounded-lg shadow">
          <h3 className="text-lg font-medium text-gray-900 dark:text-white mb-4">
            Revenue Trends
          </h3>
          <div className="h-64 bg-gray-100 dark:bg-gray-700 rounded-lg flex items-center justify-center">
            <p className="text-gray-500 dark:text-gray-400">Chart placeholder</p>
          </div>
        </div>
      </div>
    </div>
  )
}

export default Dashboard