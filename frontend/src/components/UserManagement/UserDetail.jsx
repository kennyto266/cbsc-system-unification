/**
 * User Detail Component
 * 用户详情组件
 *
 * Features:
 * - 显示用户详细信息
 * - 编辑用户信息
 * - 查看用户策略
 * - 管理用户权限
 */

import React, { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import {
  Card,
  Descriptions,
  Button,
  Space,
  Tag,
  Tabs,
  Table,
  Form,
  Input,
  Switch,
  Select,
  message,
  Modal,
} from 'antd';
import {
  EditOutlined,
  SaveOutlined,
  CancelOutlined,
  ArrowLeftOutlined,
} from '@ant-design/icons';
import { userAPI, strategyAPI } from '../../services/api';

const { TabPane } = Tabs;
const { Option } = Select;

const UserDetail = () => {
  const { userId } = useParams();
  const navigate = useNavigate();

  // State
  const [user, setUser] = useState(null);
  const [strategies, setStrategies] = useState([]);
  const [loading, setLoading] = useState(false);
  const [editing, setEditing] = useState(false);
  const [form] = Form.useForm();

  // Fetch user data
  const fetchUser = async () => {
    setLoading(true);
    try {
      const userData = await userAPI.getUser(userId);
      setUser(userData);
      form.setFieldsValue(userData);
    } catch (error) {
      message.error('获取用户信息失败: ' + error.message);
    } finally {
      setLoading(false);
    }
  };

  // Fetch user strategies
  const fetchUserStrategies = async () => {
    try {
      const response = await strategyAPI.getStrategies(1, 20, { user_id: userId });
      setStrategies(response.data || []);
    } catch (error) {
      console.error('获取用户策略失败:', error);
    }
  };

  useEffect(() => {
    fetchUser();
    fetchUserStrategies();
  }, [userId]);

  // Handle save user
  const handleSave = async () => {
    try {
      const values = await form.validateFields();
      await userAPI.updateUser(userId, values);
      message.success('用户信息更新成功');
      setEditing(false);
      fetchUser();
    } catch (error) {
      message.error('更新失败: ' + error.message);
    }
  };

  // Handle cancel edit
  const handleCancel = () => {
    setEditing(false);
    form.setFieldsValue(user);
  };

  // Strategy table columns
  const strategyColumns = [
    {
      title: '策略名称',
      dataIndex: 'name',
      key: 'name',
    },
    {
      title: '类型',
      dataIndex: 'type',
      key: 'type',
      render: (type) => <Tag>{type}</Tag>,
    },
    {
      title: '状态',
      dataIndex: 'status',
      key: 'status',
      render: (status) => (
        <Tag color={status === 'active' ? 'green' : 'default'}>
          {status}
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
        <Button
          type="link"
          onClick={() => {
            // TODO: Navigate to strategy detail
            console.log('View strategy:', record.id);
          }}
        >
          查看详情
        </Button>
      ),
    },
  ];

  if (!user) {
    return <div style={{ padding: 24 }}>加载中...</div>;
  }

  return (
    <div style={{ padding: 24 }}>
      {/* Header */}
      <div style={{ marginBottom: 24, display: 'flex', alignItems: 'center' }}>
        <Button
          icon={<ArrowLeftOutlined />}
          onClick={() => navigate('/users')}
          style={{ marginRight: 16 }}
        >
          返回用户列表
        </Button>
        <h2 style={{ margin: 0, flex: 1 }}>用户详情</h2>
        {!editing ? (
          <Button
            type="primary"
            icon={<EditOutlined />}
            onClick={() => setEditing(true)}
          >
            编辑
          </Button>
        ) : (
          <Space>
            <Button
              type="primary"
              icon={<SaveOutlined />}
              onClick={handleSave}
            >
              保存
            </Button>
            <Button
              icon={<CancelOutlined />}
              onClick={handleCancel}
            >
              取消
            </Button>
          </Space>
        )}
      </div>

      {/* User Information */}
      <Card title="基本信息" style={{ marginBottom: 24 }}>
        {editing ? (
          <Form
            form={form}
            layout="vertical"
            initialValues={user}
          >
            <Form.Item
              label="用户名"
              name="username"
              rules={[{ required: true, message: '请输入用户名' }]}
            >
              <Input />
            </Form.Item>

            <Form.Item
              label="邮箱"
              name="email"
              rules={[
                { required: true, message: '请输入邮箱' },
                { type: 'email', message: '请输入有效的邮箱地址' },
              ]}
            >
              <Input />
            </Form.Item>

            <Form.Item label="状态" name="is_active" valuePropName="checked">
              <Switch checkedChildren="启用" unCheckedChildren="禁用" />
            </Form.Item>

            <Form.Item label="管理员权限" name="is_admin" valuePropName="checked">
              <Switch checkedChildren="是" unCheckedChildren="否" />
            </Form.Item>

            <Form.Item label="风险偏好" name="risk_tolerance">
              <Select>
                <Option value="low">低风险</Option>
                <Option value="medium">中等风险</Option>
                <Option value="high">高风险</Option>
              </Select>
            </Form.Item>
          </Form>
        ) : (
          <Descriptions column={2}>
            <Descriptions.Item label="用户名">
              {user.username}
              {user.is_admin && <Tag color="red" style={{ marginLeft: 8 }}>管理员</Tag>}
            </Descriptions.Item>
            <Descriptions.Item label="邮箱">{user.email}</Descriptions.Item>
            <Descriptions.Item label="状态">
              <Tag color={user.is_active ? 'green' : 'red'}>
                {user.is_active ? '活跃' : '禁用'}
              </Tag>
            </Descriptions.Item>
            <Descriptions.Item label="用户ID">{user.id}</Descriptions.Item>
            <Descriptions.Item label="创建时间">
              {new Date(user.created_at).toLocaleString()}
            </Descriptions.Item>
            <Descriptions.Item label="最后更新">
              {user.updated_at ? new Date(user.updated_at).toLocaleString() : '-'}
            </Descriptions.Item>
            <Descriptions.Item label="风险偏好">
              {user.preferences?.risk_tolerance || '-'}
            </Descriptions.Item>
            <Descriptions.Item label="默认策略类型">
              {user.preferences?.default_strategy_type || '-'}
            </Descriptions.Item>
          </Descriptions>
        )}
      </Card>

      {/* User Activities */}
      <Card title="用户活动" style={{ marginBottom: 24 }}>
        <Tabs defaultActiveKey="strategies">
          <TabPane tab="策略列表" key="strategies">
            <Table
              columns={strategyColumns}
              dataSource={strategies}
              rowKey="id"
              pagination={{
                pageSize: 10,
                showSizeChanger: true,
                showQuickJumper: true,
              }}
            />
          </TabPane>

          <TabPane tab="登录历史" key="loginHistory">
            <p>TODO: 实现登录历史功能</p>
          </TabPane>

          <TabPane tab="操作日志" key="activityLog">
            <p>TODO: 实现操作日志功能</p>
          </TabPane>
        </Tabs>
      </Card>
    </div>
  );
};

export default UserDetail;