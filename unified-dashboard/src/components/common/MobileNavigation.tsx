import React from 'react'
import { TabBar } from 'antd-mobile'
import {
  DashboardOutlined,
  BarChartOutlined,
  MonitorOutlined,
  TrophyOutlined,
  SettingOutlined,
} from '@ant-design/icons'

interface MobileNavigationProps {
  currentPage: string
  onNavigate: (page: string) => void
  menuItems: Array<{
    key: string
    icon: React.ReactNode
    label: string
    badge?: number
  }>
}

const MobileNavigation: React.FC<MobileNavigationProps> = ({
  currentPage,
  onNavigate,
  menuItems
}) => {
  const tabBarItems = menuItems.map(item => ({
    key: item.key,
    title: item.label,
    icon: item.icon,
    badge: item.badge || undefined,
  }))

  return (
    <div className="fixed bottom-0 left-0 right-0 bg-white border-t border-gray-200 z-50 md:hidden">
      <TabBar
        activeKey={currentPage}
        onChange={onNavigate}
      >
        {tabBarItems.map(item => (
          <TabBar.Item
            key={item.key}
            title={item.title}
            icon={item.icon}
            badge={item.badge}
          />
        ))}
      </TabBar>
    </div>
  )
}

export default MobileNavigation