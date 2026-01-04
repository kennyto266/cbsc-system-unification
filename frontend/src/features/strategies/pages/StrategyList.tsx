import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { Plus, Search, Filter } from 'lucide-react';
import { Button } from 'antd';
import { StrategyControlDashboard } from '../components';

interface StrategyListProps {}

const StrategyList: React.FC<StrategyListProps> = () => {
  const navigate = useNavigate();
  const [searchTerm, setSearchTerm] = useState('');

  const handleCreateStrategy = () => {
    navigate('/strategies/new');
  };

  return (
    <div className="min-h-screen bg-gray-50 dark:bg-gray-900">
      {/* Page Header */}
      <div className="bg-white dark:bg-gray-800 border-b border-gray-200 dark:border-gray-700 px-6 py-4">
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-2xl font-bold text-gray-900 dark:text-white">
              策略管理
            </h1>
            <p className="text-sm text-gray-600 dark:text-gray-400 mt-1">
              管理和监控您的交易策略
            </p>
          </div>
          <Button
            onClick={handleCreateStrategy}
            className="bg-blue-600 hover:bg-blue-700 text-white"
          >
            <Plus className="h-4 w-4 mr-2" />
            创建策略
          </Button>
        </div>

        {/* Search and Filter Bar */}
        <div className="flex items-center gap-4 mt-4">
          <div className="relative flex-1 max-w-md">
            <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 h-4 w-4 text-gray-400" />
            <input
              type="text"
              placeholder="搜索策略..."
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              className="pl-10 pr-4 w-full px-3 py-2 bg-gray-50 dark:bg-gray-900 border border-gray-300 dark:border-gray-600 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
            />
          </div>
          <Button
            variant="outline"
            className="flex items-center gap-2"
          >
            <Filter className="h-4 w-4" />
            筛选
          </Button>
        </div>
      </div>

      {/* Main Content */}
      <div className="p-6">
        <StrategyControlDashboard className="bg-transparent shadow-none" />
      </div>
    </div>
  );
};

export default StrategyList;
