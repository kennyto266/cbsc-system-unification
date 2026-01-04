/**
 * CSS Module Transform for Jest
 * CSS 模块转换器
 */
module.exports = {
  process() {
    return {
      code: 'module.exports = {};',
    }
  },
  getCacheKey() {
    return 'cssTransform'
  },
}
