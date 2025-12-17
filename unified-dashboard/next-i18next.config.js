/**
 * Next.js i18n Configuration
 * CBSC量化交易系統的國際化配置
 */

module.exports = {
  i18n: {
    defaultLocale: 'zh-HK',
    locales: ['zh-HK', 'zh-CN', 'en-US'],
    localeDetection: true,
    domains: [
      {
        domain: 'cbsc.com.hk',
        defaultLocale: 'zh-HK',
      },
      {
        domain: 'cbsc.com.cn',
        defaultLocale: 'zh-CN',
      },
      {
        domain: 'cbsc.com',
        defaultLocale: 'en-US',
      },
    ],
  },
}