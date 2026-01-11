import React from 'react'
import {
  GithubOutlined,
  TwitterOutlined,
  WechatOutlined,
  MailOutlined,
  LinkOutlined,
  HeartOutlined,
  CopyrightOutlined
} from '@ant-design/icons'
import { Row, Col, Space, Divider } from 'antd'
import { motion } from 'framer-motion'

const Footer: React.FC = () => {
  const currentYear = new Date().getFullYear()

  const footerLinks = {
    product: [
      { name: '功能介绍', href: '/features' },
      { name: '定价方案', href: '/pricing' },
      { name: '更新日志', href: '/changelog' },
      { name: '路线图', href: '/roadmap' },
    ],
    resources: [
      { name: '文档中心', href: '/docs' },
      { name: 'API参考', href: '/api' },
      { name: '视频教程', href: '/tutorials' },
      { name: '社区论坛', href: '/community' },
    ],
    company: [
      { name: '关于我们', href: '/about' },
      { name: '联系我们', href: '/contact' },
      { name: '加入我们', href: '/careers' },
      { name: '合作伙伴', href: '/partners' },
    ],
    legal: [
      { name: '服务条款', href: '/terms' },
      { name: '隐私政策', href: '/privacy' },
      { name: '安全声明', href: '/security' },
      { name: '合规说明', href: '/compliance' },
    ],
  }

  const socialLinks = [
    {
      icon: <GithubOutlined />,
      href: 'https://github.com/cbsc-team',
      title: 'GitHub',
    },
    {
      icon: <TwitterOutlined />,
      href: 'https://twitter.com/cbsc_official',
      title: 'Twitter',
    },
    {
      icon: <WechatOutlined />,
      href: '#',
      title: '微信公众号',
    },
    {
      icon: <MailOutlined />,
      href: 'mailto:support@cbsc.com',
      title: '邮箱',
    },
  ]

  return (
    <footer className="bg-gray-50 dark:bg-gray-900 border-t border-gray-200 dark:border-gray-800">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-12">
        {/* Main Footer Content */}
        <Row gutter={[32, 32]}>
          {/* Brand and Description */}
          <Col xs={24} sm={12} lg={6}>
            <motion.div
              initial={{ opacity: 0, y: 20 }}
              whileInView={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.5 }}
            >
              <div className="flex items-center space-x-2 mb-4">
                <div className="w-8 h-8 bg-gradient-to-br from-blue-500 to-blue-600 rounded-lg flex items-center justify-center">
                  <span className="text-white font-bold text-lg">C</span>
                </div>
                <span className="text-lg font-bold text-gray-900 dark:text-white">CBSC</span>
              </div>
              <p className="text-sm text-gray-600 dark:text-gray-400 mb-4">
                专业的量化交易策略管理平台，为投资者提供智能化的交易解决方案。
              </p>
              <Space size="middle">
                {socialLinks.map((social, index) => (
                  <motion.a
                    key={index}
                    href={social.href}
                    title={social.title}
                    className="text-gray-400 hover:text-blue-500 dark:hover:text-blue-400 transition-colors"
                    whileHover={{ scale: 1.2 }}
                    whileTap={{ scale: 0.9 }}
                  >
                    {social.icon}
                  </motion.a>
                ))}
              </Space>
            </motion.div>
          </Col>

          {/* Product Links */}
          <Col xs={24} sm={12} lg={6}>
            <motion.div
              initial={{ opacity: 0, y: 20 }}
              whileInView={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.5, delay: 0.1 }}
            >
              <h3 className="text-sm font-semibold text-gray-900 dark:text-white uppercase tracking-wider mb-4">
                产品
              </h3>
              <ul className="space-y-2">
                {footerLinks.product.map((link, index) => (
                  <li key={index}>
                    <a
                      href={link.href}
                      className="text-sm text-gray-600 dark:text-gray-400 hover:text-blue-600 dark:hover:text-blue-400 transition-colors"
                    >
                      {link.name}
                    </a>
                  </li>
                ))}
              </ul>
            </motion.div>
          </Col>

          {/* Resources Links */}
          <Col xs={24} sm={12} lg={6}>
            <motion.div
              initial={{ opacity: 0, y: 20 }}
              whileInView={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.5, delay: 0.2 }}
            >
              <h3 className="text-sm font-semibold text-gray-900 dark:text-white uppercase tracking-wider mb-4">
                资源
              </h3>
              <ul className="space-y-2">
                {footerLinks.resources.map((link, index) => (
                  <li key={index}>
                    <a
                      href={link.href}
                      className="text-sm text-gray-600 dark:text-gray-400 hover:text-blue-600 dark:hover:text-blue-400 transition-colors"
                    >
                      {link.name}
                    </a>
                  </li>
                ))}
              </ul>
            </motion.div>
          </Col>

          {/* Company & Legal Links */}
          <Col xs={24} sm={12} lg={6}>
            <Row gutter={[32, 32]}>
              <Col span={12}>
                <motion.div
                  initial={{ opacity: 0, y: 20 }}
                  whileInView={{ opacity: 1, y: 0 }}
                  transition={{ duration: 0.5, delay: 0.3 }}
                >
                  <h3 className="text-sm font-semibold text-gray-900 dark:text-white uppercase tracking-wider mb-4">
                    公司
                  </h3>
                  <ul className="space-y-2">
                    {footerLinks.company.map((link, index) => (
                      <li key={index}>
                        <a
                          href={link.href}
                          className="text-sm text-gray-600 dark:text-gray-400 hover:text-blue-600 dark:hover:text-blue-400 transition-colors"
                        >
                          {link.name}
                        </a>
                      </li>
                    ))}
                  </ul>
                </motion.div>
              </Col>
              <Col span={12}>
                <motion.div
                  initial={{ opacity: 0, y: 20 }}
                  whileInView={{ opacity: 1, y: 0 }}
                  transition={{ duration: 0.5, delay: 0.4 }}
                >
                  <h3 className="text-sm font-semibold text-gray-900 dark:text-white uppercase tracking-wider mb-4">
                    法律
                  </h3>
                  <ul className="space-y-2">
                    {footerLinks.legal.map((link, index) => (
                      <li key={index}>
                        <a
                          href={link.href}
                          className="text-sm text-gray-600 dark:text-gray-400 hover:text-blue-600 dark:hover:text-blue-400 transition-colors"
                        >
                          {link.name}
                        </a>
                      </li>
                    ))}
                  </ul>
                </motion.div>
              </Col>
            </Row>
          </Col>
        </Row>

        <Divider className="my-8 border-gray-200 dark:border-gray-700" />

        {/* Bottom Footer */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          whileInView={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.5, delay: 0.5 }}
          className="flex flex-col sm:flex-row justify-between items-center space-y-4 sm:space-y-0"
        >
          <div className="flex items-center space-x-2 text-sm text-gray-600 dark:text-gray-400">
            <CopyrightOutlined />
            <span>{currentYear} CBSC Team. All rights reserved.</span>
          </div>

          <div className="flex items-center space-x-4 text-sm">
            <span className="text-gray-600 dark:text-gray-400">
              Made with <HeartOutlined className="text-red-500" /> by CBSC Team
            </span>
            <span className="text-gray-400">|</span>
            <span className="text-gray-600 dark:text-gray-400">
              Version 2.0.1
            </span>
          </div>
        </motion.div>
      </div>

      {/* Back to Top Button */}
      <motion.button
        onClick={() => window.scrollTo({ top: 0, behavior: 'smooth' })}
        className="fixed bottom-8 right-8 w-10 h-10 bg-blue-500 hover:bg-blue-600 text-white rounded-full shadow-lg flex items-center justify-center transition-colors z-10"
        initial={{ opacity: 0, scale: 0 }}
        animate={{ opacity: 1, scale: 1 }}
        whileHover={{ y: -2 }}
        whileTap={{ scale: 0.95 }}
      >
        <LinkOutlined className="transform rotate-90" />
      </motion.button>
    </footer>
  )
}

export default Footer