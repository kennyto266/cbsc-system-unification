import React from 'react'

const Footer: React.FC = () => {
  const currentYear = new Date().getFullYear()

  return (
    <footer className="bg-white dark:bg-gray-900 border-t border-gray-200 dark:border-gray-800">
      <div className="mx-auto max-w-7xl px-4 sm:px-6 lg:px-8">
        <div className="py-4">
          <p className="text-center text-sm text-gray-500 dark:text-gray-400">
            © {currentYear} Square UI. All rights reserved.
          </p>
        </div>
      </div>
    </footer>
  )
}

export default Footer