import React from 'react'

const ReportsActivity: React.FC = () => {
  return (
    <div>
      <h2 className="text-2xl font-bold text-gray-900 dark:text-white mb-6">
        Activity Logs
      </h2>

      {/* Filter options */}
      <div className="mb-6 flex flex-col sm:flex-row gap-4">
        <input
          type="search"
          placeholder="Search activities..."
          className="flex-1 px-4 py-2 border border-gray-300 dark:border-gray-700 rounded-lg bg-white dark:bg-gray-800 text-gray-900 dark:text-white"
        />
        <select className="px-4 py-2 border border-gray-300 dark:border-gray-700 rounded-lg bg-white dark:bg-gray-800 text-gray-900 dark:text-white">
          <option>All Activities</option>
          <option>Login</option>
          <option>File Upload</option>
          <option>Settings Change</option>
          <option>User Management</option>
        </select>
        <select className="px-4 py-2 border border-gray-300 dark:border-gray-700 rounded-lg bg-white dark:bg-gray-800 text-gray-900 dark:text-white">
          <option>Last 24 hours</option>
          <option>Last 7 days</option>
          <option>Last 30 days</option>
        </select>
      </div>

      {/* Activity timeline */}
      <div className="bg-white dark:bg-gray-800 shadow rounded-lg">
        <div className="p-6">
          <div className="flow-root">
            <ul className="-mb-8">
              {[1, 2, 3, 4, 5, 6, 7].map(i => (
                <li key={i}>
                  <div className="relative pb-8">
                    {i !== 7 && (
                      <span
                        className="absolute top-4 left-4 -ml-px h-full w-0.5 bg-gray-200 dark:bg-gray-700"
                        aria-hidden="true"
                      />
                    )}
                    <div className="relative flex space-x-3">
                      <div>
                        <span className="h-8 w-8 rounded-full bg-primary-500 flex items-center justify-center ring-8 ring-white dark:ring-gray-900">
                          <span className="text-white text-sm font-medium">
                            {i === 1 ? 'L' : i === 2 ? 'U' : i === 3 ? 'S' : i === 4 ? 'F' : i === 5 ? 'D' : i === 6 ? 'C' : 'A'}
                          </span>
                        </span>
                      </div>
                      <div className="flex-1 min-w-0 pt-1.5 flex justify-between space-x-4">
                        <div>
                          <p className="text-sm text-gray-900 dark:text-white">
                            {i === 1 && 'User logged in'}
                            {i === 2 && 'Updated user profile'}
                            {i === 3 && 'Changed system settings'}
                            {i === 4 && 'Uploaded file: report.pdf'}
                            {i === 5 && 'Deleted user: john.doe'}
                            {i === 6 && 'Created new role: Viewer'}
                            {i === 7 && 'Admin access granted'}
                          </p>
                          <p className="text-sm text-gray-500 dark:text-gray-400">
                            by User {i} • {i} hour{i !== 1 ? 's' : ''} ago
                          </p>
                        </div>
                        <div className="text-right text-sm whitespace-nowrap text-gray-500 dark:text-gray-400">
                          <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-gray-100 dark:bg-gray-700 text-gray-800 dark:text-gray-200">
                            {i === 1 ? 'Auth' : i === 2 ? 'Update' : i === 3 ? 'Config' : i === 4 ? 'File' : i === 5 ? 'Delete' : i === 6 ? 'Create' : 'Security'}
                          </span>
                        </div>
                      </div>
                    </div>
                  </div>
                </li>
              ))}
            </ul>
          </div>

          {/* Load more */}
          <div className="mt-6 flex justify-center">
            <button className="px-4 py-2 border border-gray-300 dark:border-gray-700 rounded-lg text-sm font-medium text-gray-700 dark:text-gray-300 hover:bg-gray-50 dark:hover:bg-gray-700 transition-colors">
              Load More Activities
            </button>
          </div>
        </div>
      </div>
    </div>
  )
}

export default ReportsActivity