// CSS transformation for Jest
module.exports = {
  process() {
    return {
      code: 'module.exports = {};'
    }
  },
  getCacheKey() {
    // Return a string version of the CSS to cache
    return 'css-transform'
  },
}