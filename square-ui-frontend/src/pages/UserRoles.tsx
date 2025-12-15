import React from 'react'

const UserRoles: React.FC = () => {
  return (
    <div>
      <h2 className="text-2xl font-bold text-gray-900 dark:text-white mb-6">
        Roles & Permissions
      </h2>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Roles list */}
        <div className="lg:col-span-1">
          <div className="bg-white dark:bg-gray-800 shadow rounded-lg">
            <div className="px-4 py-5 sm:p-6">
              <h3 className="text-lg font-medium text-gray-900 dark:text-white mb-4">
                System Roles
              </h3>
              <div className="space-y-2">
                {['Administrator', 'Manager', 'User', 'Viewer'].map(role => (
                  <button
                    key={role}
                    className="w-full text-left px-4 py-2 rounded-lg hover:bg-gray-50 dark:hover:bg-gray-700 transition-colors"
                  >
                    {role}
                  </button>
                ))}
              </div>
              <button className="mt-4 w-full px-4 py-2 bg-primary-600 text-white rounded-lg hover:bg-primary-700 transition-colors">
                Add Role
              </button>
            </div>
          </div>
        </div>

        {/* Role details */}
        <div className="lg:col-span-2">
          <div className="bg-white dark:bg-gray-800 shadow rounded-lg">
            <div className="px-4 py-5 sm:p-6">
              <h3 className="text-lg font-medium text-gray-900 dark:text-white mb-4">
                Role Permissions: Administrator
              </h3>

              <div className="space-y-6">
                {['User Management', 'Reports', 'Settings', 'Analytics'].map(section => (
                  <div key={section}>
                    <h4 className="text-sm font-medium text-gray-900 dark:text-white mb-3">
                      {section}
                    </h4>
                    <div className="space-y-2">
                      {['Read', 'Write', 'Delete', 'Admin'].map(permission => (
                        <label key={permission} className="flex items-center">
                          <input
                            type="checkbox"
                            className="h-4 w-4 text-primary-600 focus:ring-primary-500 border-gray-300 dark:border-gray-700 rounded"
                            defaultChecked={permission === 'Read' || permission === 'Write'}
                          />
                          <span className="ml-2 text-sm text-gray-700 dark:text-gray-300">
                            {permission} access
                          </span>
                        </label>
                      ))}
                    </div>
                  </div>
                ))}
              </div>

              <div className="mt-6 flex justify-end">
                <button className="px-4 py-2 bg-primary-600 text-white rounded-lg hover:bg-primary-700 transition-colors">
                  Save Changes
                </button>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}

export default UserRoles