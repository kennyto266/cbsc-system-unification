/**
 * Share Manager Component
 * 分享管理組件
 */

import React, { useState, useEffect } from 'react';
import {
  ShareIcon,
  EyeIcon,
  ArrowDownTrayIcon,
  PencilIcon,
  TrashIcon,
  LinkIcon,
  ClockIcon,
  ShieldCheckIcon,
  UserGroupIcon
} from '@heroicons/react/24/outline';
import { Button } from '../ui/Button';
import { Modal } from '../ui/Modal';
import { Alert } from '../ui/Alert';
import { Loading } from '../ui/Loading';
import { Badge } from '../ui/Badge';
import { Card } from '../ui/Card';
import { exportService } from '../../services/exportService';
import { DataExporter } from './DataExporter';

interface ShareLink {
  id: string;
  token: string;
  url: string;
  strategyId: string;
  strategyName: string;
  createdAt: string;
  expiresAt?: string;
  password?: boolean;
  allowDownload: boolean;
  allowEdit: boolean;
  maxViews?: number;
  viewCount: number;
  lastAccessed?: string;
  status: 'active' | 'expired' | 'revoked';
}

interface ShareManagerProps {
  isOpen: boolean;
  onClose: () => void;
  strategyId?: string;
  onShareCreate?: (link: ShareLink) => void;
}

export const ShareManager: React.FC<ShareManagerProps> = ({
  isOpen,
  onClose,
  strategyId,
  onShareCreate
}) => {
  const [shares, setShares] = useState<ShareLink[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [selectedShare, setSelectedShare] = useState<ShareLink | null>(null);
  const [showDeleteConfirm, setShowDeleteConfirm] = useState(false);
  const [showCreateModal, setShowCreateModal] = useState(false);

  // Load shares when modal opens
  useEffect(() => {
    if (isOpen) {
      loadShares();
    }
  }, [isOpen, strategyId]);

  // Load shared links
  const loadShares = async () => {
    setLoading(true);
    setError(null);

    try {
      // In a real implementation, this would fetch from an API
      // For now, we'll use mock data
      const mockShares: ShareLink[] = [
        {
          id: '1',
          token: 'abc123',
          url: 'https://cbsc.example.com/shared/abc123',
          strategyId: 'strategy-1',
          strategyName: 'RSI 動量策略',
          createdAt: '2024-01-15T10:00:00Z',
          expiresAt: '2024-02-15T10:00:00Z',
          password: true,
          allowDownload: true,
          allowEdit: false,
          maxViews: 100,
          viewCount: 23,
          lastAccessed: '2024-01-20T15:30:00Z',
          status: 'active'
        },
        {
          id: '2',
          token: 'def456',
          url: 'https://cbsc.example.com/shared/def456',
          strategyId: 'strategy-1',
          strategyName: 'RSI 動量策略',
          createdAt: '2024-01-10T10:00:00Z',
          password: false,
          allowDownload: true,
          allowEdit: true,
          status: 'active'
        }
      ];

      // Filter by strategy if provided
      const filteredShares = strategyId
        ? mockShares.filter(s => s.strategyId === strategyId)
        : mockShares;

      setShares(filteredShares);
    } catch (err) {
      console.error('Failed to load shares:', err);
      setError('加載分享鏈接失敗');
    } finally {
      setLoading(false);
    }
  };

  // Revoke share
  const handleRevokeShare = async (shareId: string) => {
    try {
      // In a real implementation, this would call an API
      setShares(prev => prev.map(s =>
        s.id === shareId ? { ...s, status: 'revoked' as const } : s
      ));
      setShowDeleteConfirm(false);
    } catch (err) {
      console.error('Failed to revoke share:', err);
      setError('撤銷分享鏈接失敗');
    }
  };

  // Copy share link
  const handleCopyLink = async (url: string) => {
    try {
      await navigator.clipboard.writeText(url);
      // Show success message
      setError('鏈接已複製到剪貼板');
      setTimeout(() => setError(null), 3000);
    } catch (err) {
      console.error('Failed to copy link:', err);
      setError('複製失敗');
    }
  };

  // Get status badge
  const getStatusBadge = (status: ShareLink['status']) => {
    const config = {
      active: {
        color: 'bg-green-100 text-green-800 dark:bg-green-900/30 dark:text-green-400',
        label: '活躍'
      },
      expired: {
        color: 'bg-gray-100 text-gray-800 dark:bg-gray-800/50 dark:text-gray-300',
        label: '已過期'
      },
      revoked: {
        color: 'bg-red-100 text-red-800 dark:bg-red-900/30 dark:text-red-400',
        label: '已撤銷'
      }
    };

    const { color, label } = config[status];
    return <Badge className={color}>{label}</Badge>;
  };

  // Format date
  const formatDate = (dateString: string) => {
    return new Date(dateString).toLocaleDateString('zh-TW', {
      year: 'numeric',
      month: '2-digit',
      day: '2-digit',
      hour: '2-digit',
      minute: '2-digit'
    });
  };

  return (
    <Modal
      isOpen={isOpen}
      onClose={onClose}
      title="分享管理"
      size="lg"
    >
      <div className="space-y-6">
        {/* Header Actions */}
        <div className="flex items-center justify-between">
          <div>
            <h3 className="text-lg font-medium text-gray-900 dark:text-white">
              分享鏈接管理
            </h3>
            <p className="text-sm text-gray-600 dark:text-gray-400 mt-1">
              管理您的策略分享鏈接
            </p>
          </div>
          <Button
            variant="primary"
            icon={ShareIcon}
            onClick={() => setShowCreateModal(true)}
          >
            創建分享
          </Button>
        </div>

        {/* Error Alert */}
        {error && (
          <Alert
            variant={error.includes('複製') ? 'success' : 'error'}
            title={error.includes('複製') ? '成功' : '錯誤'}
            description={error}
            onClose={() => setError(null)}
          />
        )}

        {/* Loading State */}
        {loading && (
          <div className="flex items-center justify-center py-8">
            <Loading size="lg" text="載入中..." />
          </div>
        )}

        {/* Share List */}
        {!loading && shares.length === 0 ? (
          <Card className="p-8 text-center">
            <ShareIcon className="mx-auto h-12 w-12 text-gray-400 dark:text-gray-600" />
            <h3 className="mt-4 text-lg font-medium text-gray-900 dark:text-white">
              沒有分享鏈接
            </h3>
            <p className="mt-2 text-sm text-gray-600 dark:text-gray-400">
              創建您的第一個分享鏈接來分享策略
            </p>
            <Button
              variant="primary"
              icon={ShareIcon}
              className="mt-4"
              onClick={() => setShowCreateModal(true)}
            >
              創建分享
            </Button>
          </Card>
        ) : (
          !loading && (
            <div className="space-y-4">
              {shares.map((share) => (
                <Card key={share.id} className="p-4">
                  <div className="flex items-start justify-between">
                    {/* Share Info */}
                    <div className="flex-1">
                      <div className="flex items-center space-x-3 mb-2">
                        <h4 className="font-medium text-gray-900 dark:text-white">
                          {share.strategyName}
                        </h4>
                        {getStatusBadge(share.status)}
                        {share.password && (
                          <Badge className="bg-yellow-100 text-yellow-800 dark:bg-yellow-900/30 dark:text-yellow-400">
                            <ShieldCheckIcon className="w-3 h-3 mr-1" />
                            已加密
                          </Badge>
                        )}
                      </div>

                      {/* Share URL */}
                      <div className="flex items-center space-x-2 mb-3">
                        <LinkIcon className="w-4 h-4 text-gray-400" />
                        <code className="text-sm text-gray-600 dark:text-gray-400 bg-gray-100 dark:bg-gray-800 px-2 py-1 rounded">
                          {share.url}
                        </code>
                      </div>

                      {/* Share Details */}
                      <div className="grid grid-cols-2 md:grid-cols-4 gap-4 text-sm">
                        <div>
                          <span className="text-gray-500 dark:text-gray-400">創建時間</span>
                          <p className="text-gray-900 dark:text-white">
                            {formatDate(share.createdAt)}
                          </p>
                        </div>
                        {share.expiresAt && (
                          <div>
                            <span className="text-gray-500 dark:text-gray-400">過期時間</span>
                            <p className="text-gray-900 dark:text-white">
                              {formatDate(share.expiresAt)}
                            </p>
                          </div>
                        )}
                        <div>
                          <span className="text-gray-500 dark:text-gray-400">訪問次數</span>
                          <p className="text-gray-900 dark:text-white">
                            {share.viewCount}
                            {share.maxViews && ` / ${share.maxViews}`}
                          </p>
                        </div>
                        <div>
                          <span className="text-gray-500 dark:text-gray-400">權限</span>
                          <div className="flex space-x-1 mt-1">
                            {share.allowDownload && (
                              <ArrowDownTrayIcon className="w-4 h-4 text-gray-600 dark:text-gray-400" title="允許下載" />
                            )}
                            {share.allowEdit && (
                              <PencilIcon className="w-4 h-4 text-gray-600 dark:text-gray-400" title="允許編輯" />
                            )}
                          </div>
                        </div>
                      </div>

                      {share.lastAccessed && (
                        <div className="mt-3 text-xs text-gray-500 dark:text-gray-400">
                          最後訪問: {formatDate(share.lastAccessed)}
                        </div>
                      )}
                    </div>

                    {/* Actions */}
                    <div className="flex items-center space-x-2 ml-4">
                      <Button
                        variant="ghost"
                        size="sm"
                        icon={<LinkIcon />}
                        onClick={() => handleCopyLink(share.url)}
                        title="複製鏈接"
                      />
                      {share.status === 'active' && (
                        <Button
                          variant="ghost"
                          size="sm"
                          icon={<EyeIcon />}
                          onClick={() => window.open(share.url, '_blank')}
                          title="預覽"
                        />
                      )}
                      <Button
                        variant="ghost"
                        size="sm"
                        icon={<TrashIcon />}
                        onClick={() => {
                          setSelectedShare(share);
                          setShowDeleteConfirm(true);
                        }}
                        className="text-red-600 hover:text-red-900 dark:text-red-400 dark:hover:text-red-300"
                        title="撤銷"
                      />
                    </div>
                  </div>
                </Card>
              ))}
            </div>
          )
        )}

        {/* Delete Confirmation Modal */}
        {showDeleteConfirm && selectedShare && (
          <Modal
            isOpen={showDeleteConfirm}
            onClose={() => {
              setShowDeleteConfirm(false);
              setSelectedShare(null);
            }}
            title="撤銷分享鏈接"
            size="sm"
          >
            <div className="space-y-4">
              <p className="text-gray-700 dark:text-gray-300">
                確定要撤銷策略 "{selectedShare.strategyName}" 的分享鏈接嗎？
              </p>
              <p className="text-sm text-gray-600 dark:text-gray-400">
                此操作無法撤銷。鏈接將立即失效，無法再訪問。
              </p>
              <div className="flex justify-end space-x-3">
                <Button
                  variant="outline"
                  onClick={() => {
                    setShowDeleteConfirm(false);
                    setSelectedShare(null);
                  }}
                >
                  取消
                </Button>
                <Button
                  variant="danger"
                  onClick={() => {
                    if (selectedShare) {
                      handleRevokeShare(selectedShare.id);
                    }
                  }}
                >
                  撤銷
                </Button>
              </div>
            </div>
          </Modal>
        )}

        {/* Create Share Modal */}
        {showCreateModal && (
          <DataExporter
            isOpen={showCreateModal}
            onClose={() => setShowCreateModal(false)}
            data={{ id: strategyId }}
            title="分享策略"
            type="strategy"
            onExportComplete={() => {
              setShowCreateModal(false);
              loadShares();
            }}
          />
        )}
      </div>
    </Modal>
  );
};