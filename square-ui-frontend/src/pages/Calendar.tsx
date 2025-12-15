import React from 'react'

const Calendar: React.FC = () => {
  return (
    <div>
      <h2 className="text-2xl font-bold text-gray-900 dark:text-white mb-6">
        Calendar
      </h2>

      {/* Calendar view switcher */}
      <div className="mb-6 flex items-center justify-between">
        <div className="flex items-center space-x-2">
          <button className="px-3 py-2 text-sm font-medium text-white bg-primary-600 rounded-lg hover:bg-primary-700 transition-colors">
            Month
          </button>
          <button className="px-3 py-2 text-sm font-medium text-gray-700 dark:text-gray-300 bg-white dark:bg-gray-800 border border-gray-300 dark:border-gray-700 rounded-lg hover:bg-gray-50 dark:hover:bg-gray-700 transition-colors">
            Week
          </button>
          <button className="px-3 py-2 text-sm font-medium text-gray-700 dark:text-gray-300 bg-white dark:bg-gray-800 border border-gray-300 dark:border-gray-700 rounded-lg hover:bg-gray-50 dark:hover:bg-gray-700 transition-colors">
            Day
          </button>
        </div>
        <button className="px-4 py-2 bg-primary-600 text-white rounded-lg hover:bg-primary-700 transition-colors">
          New Event
        </button>
      </div>

      {/* Calendar grid */}
      <div className="bg-white dark:bg-gray-800 shadow rounded-lg">
        <div className="p-6">
          {/* Calendar header */}
          <div className="flex items-center justify-between mb-6">
            <h3 className="text-lg font-medium text-gray-900 dark:text-white">
              December 2025
            </h3>
            <div className="flex items-center space-x-2">
              <button className="p-2 hover:bg-gray-100 dark:hover:bg-gray-700 rounded-lg transition-colors">
                <svg className="h-5 w-5 text-gray-500" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 19l-7-7 7-7" />
                </svg>
              </button>
              <button className="p-2 hover:bg-gray-100 dark:hover:bg-gray-700 rounded-lg transition-colors">
                <svg className="h-5 w-5 text-gray-500" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5l7 7-7 7" />
                </svg>
              </button>
            </div>
          </div>

          {/* Days of week */}
          <div className="grid grid-cols-7 gap-px bg-gray-200 dark:bg-gray-700">
            {['Sun', 'Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat'].map(day => (
              <div key={day} className="bg-gray-50 dark:bg-gray-900 px-2 py-3 text-center text-xs font-medium text-gray-700 dark:text-gray-300">
                {day}
              </div>
            ))}
          </div>

          {/* Calendar days */}
          <div className="grid grid-cols-7 gap-px bg-gray-200 dark:bg-gray-700">
            {Array.from({ length: 35 }, (_, i) => {
              const dayNumber = i - 5
              const isCurrentMonth = dayNumber >= 1 && dayNumber <= 31
              const isToday = dayNumber === 15
              const hasEvent = [5, 8, 15, 22, 28].includes(dayNumber)

              return (
                <div
                  key={i}
                  className={`
                    bg-white dark:bg-gray-900 p-2 min-h-[100px]
                    ${!isCurrentMonth ? 'bg-gray-50 dark:bg-gray-800' : ''}
                    ${isToday ? 'ring-2 ring-primary-500' : ''}
                  `}
                >
                  <div className={`
                    text-sm font-medium mb-1
                    ${!isCurrentMonth ? 'text-gray-400 dark:text-gray-600' : 'text-gray-900 dark:text-white'}
                    ${isToday ? 'text-primary-600 dark:text-primary-400' : ''}
                  `}>
                    {isCurrentMonth ? dayNumber : (dayNumber < 1 ? 30 + dayNumber : dayNumber - 31)}
                  </div>
                  {hasEvent && isCurrentMonth && (
                    <div className="space-y-1">
                      <div className="text-xs p-1 bg-primary-100 dark:bg-primary-900/30 text-primary-700 dark:text-primary-300 rounded truncate">
                        {dayNumber === 5 && 'Team Meeting'}
                        {dayNumber === 8 && 'Review'}
                        {dayNumber === 15 && 'Deadline'}
                        {dayNumber === 22 && 'Conference'}
                        {dayNumber === 28 && 'Planning'}
                      </div>
                    </div>
                  )}
                </div>
              )
            })}
          </div>
        </div>
      </div>
    </div>
  )
}

export default Calendar