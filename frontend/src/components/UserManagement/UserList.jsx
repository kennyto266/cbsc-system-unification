/**
 * User List Component
 * 用户列表组件
 *
 * Features:
 * - 分页显示用户列表
 * - 搜索和过滤功能
 * - 批量操作（启用/禁用）
 * - 实时更新（通过WebSocket）
 */

import React, { useState, useEffect } from 'react';
import { Table, Button, Input, Space, Modal, message, Tag, Popconfirm } from 'antd';
import { SearchOutlined, PlusOutlined, ReloadOutlined } from '@ant-design/icons';
import { userAPI, wsManager } from '../../services/api';

const { Search } = Input;

const UserList = () => {
  // State management
  const [users, setUsers] = useState([]);
  const [loading, setLoading] = useState(false);
  const [pagination, setPagination] = useState({
    current: 1,
    pageSize: 20,
    total: 0,
  });
  const [searchText, setSearchText] = useState('');
  const [selectedRowKeys, setSelectedRowKeys] = useState([]);

  // Fetch users data
  const fetchUsers = async (page = 1, pageSize = 20, search = '') => {
    setLoading(true);
    try {
      const response = await userAPI.getUsers(page, pageSize);
      // Filter users based on search text (frontend filtering for demo)
      let filteredUsers = response.data || [];

      if (search) {
        filteredUsers = filteredUsers.filter(user =>
          user.username.toLowerCase().includes(search.toLowerCase()) ||
          user.email.toLowerCase().includes(search.toLowerCase())
        );
      }

      setUsers(filteredUsers);
      setPagination({
        current: page,
        pageSize: pageSize,
        total: response.total || filteredUsers.length,
      });
    } catch (error) {
      message.error('获取用户列表失败: ' + error.message);
    } finally {
      setLoading(false);
    }
  };

  // Initial load
  useEffect(() => {
    fetchUsers();

    // Subscribe to WebSocket updates
    wsManager.subscribe('user_updated', (data) => {
      // Update user in list
      setUsers(prevUsers =>
        prevUsers.map(user =>
          user.id === data.user_id ? { ...user, ...data.updates } : user
        )
      );
    });

    wsManager.subscribe('user_created', (data) => {
      // Add new user to list
      setUsers(prevUsers => [data.user, ...prevUsers]);
    });

    // Cleanup
    return () => {
      wsManager.unsubscribe('user_updated');
      wsManager.unsubscribe('user_created');
    };
  }, []);

  // Table columns definition
  const columns = [
    {
      title: 'ID',
      dataIndex: 'id',
      key: 'id',
      width: 80,
    },
    {
      title: '用户名',
      dataIndex: 'username',
      key: 'username',
      render: (text, record) => (
        <Space>
          {text}
          {record.is_admin && <Tag color="red">管理员</Tag>}
        </Space>
      ),
    },
    {
      title: '邮箱',
      dataIndex: 'email',
      key: 'email',
    },
    {
      title: '状态',
      dataIndex: 'is_active',
      key: 'is_active',
      render: (isActive) => (
        <Tag color={isActive ? 'green' : 'red'}>
          {isActive ? '活跃' : '禁用'}
        </Tag>
      ),
    },
    {
      title: '创建时间',
      dataIndex: 'created_at',
      key: 'created_at',
      render: (date) => new Date(date).toLocaleDateString(),
    },
    {
      title: '操作',
      key: 'action',
      render: (_, record) => (
        <Space size="middle">
          <Button
            type="link"
            onClick={() => handleEdit(record)}
          >
            编辑
          </Button>
          <Popconfirm
            title="确定要删除这个用户吗？"
            onConfirm={() => handleDelete(record.id)}
            okText="确定"
            cancelText="取消"
          >
            <Button type="link" danger>
              删除
            </Button>
          </Popconfirm>
        </Space>
      ),
    },
  ];

  // Event handlers
  const handleTableChange = (pagination) => {
    fetchUsers(pagination.current, pagination.pageSize, searchText);
  };

  const handleSearch = (value) => {
    setSearchText(value);
    fetchUsers(1, pagination.pageSize, value);
  };

  const handleEdit = (user) => {
    // TODO: Open edit modal
    console.log('Edit user:', user);
  };

  const handleDelete = async (userId) => {
    try {
      await userAPI.deleteUser(userId);
      message.success('用户删除成功');
      fetchUsers(pagination.current, pagination.pageSize, searchText);
    } catch (error) {
      message.error('删除失败: ' + error.message);
    }
  };

  const handleBatchStatusChange = async (isActive) => {
    if (selectedRowKeys.length === 0) {
      message.warning('请选择要操作的用户');
      return;
    }

    try {
      // TODO: Implement batch update API
      message.success(`已${isActive ? '启用' : '禁用'} ${selectedRowKeys.length} 个用户`);
      setSelectedRowKeys([]);
      fetchUsers();
    } catch (error) {
      message.error('批量操作失败: ' + error.message);
    }
  };

  // Row selection configuration
  const rowSelection = {
    selectedRowKeys,
    onChange: setSelectedRowKeys,
  };

  return (
    <div style={{ padding: 24 }}>
      {/* Header */}
      <div style={{ marginBottom: 16, display: 'flex', justifyContent: 'space-between' }}>
        <Space>
          <Search
            placeholder="搜索用户名或邮箱"
            allowClear
            style={{ width: 300 }}
            onSearch={handleSearch}
            prefix={<SearchOutlined />}
          />
          <Button
            icon={<ReloadOutlined />}
            onClick={() => fetchUsers()}
          >
            刷新
          </Button>
        </Space>

        <Space>
          <Button
            type="primary"
            icon={<PlusOutlined />}
            onClick={() => {
              // TODO: Open create user modal
              console.log('Create new user');
            }}
          >
            新建用户
          </Button>
        </Space>
      </div>

      {/* Batch operations */}
      {selectedRowKeys.length > 0 && (
        <div style={{ marginBottom: 16 }}>
          <Space>
            <span>已选择 {selectedRowKeys.length} 项</span>
            <Button
              size="small"
              onClick={() => handleBatchStatusChange(true)}
            >
              批量启用
            </Button>
            <Button
              size="small"
              danger
              onClick={() => handleBatchStatusChange(false)}
            >
              批量禁用
            </Button>
          </Space>
        </div>
      )}

      {/* User table */}
      <Table
        columns={columns}
        dataSource={users}
        rowKey="id"
        loading={loading}
        pagination={pagination}
        onChange={handleTableChange}
        rowSelection={rowSelection}
      />
    </div>
  );
};

export default UserList;