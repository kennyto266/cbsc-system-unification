// Bundle Size Analysis Tool
const { execSync } = require('child_process');
const fs = require('fs');
const path = require('path');

class BundleAnalyzer {
  constructor() {
    this.results = {
      totalSize: 0,
      bundles: [],
      dependencies: {},
      recommendations: []
    };
  }

  async analyze() {
    console.log('📦 Analyzing bundle sizes...\n');

    // Check if dist directory exists
    const distPath = path.join(__dirname, '../../dist');
    if (!fs.existsSync(distPath)) {
      console.log('❌ Build output not found. Running build first...');
      try {
        execSync('npm run build', { cwd: path.join(__dirname, '../..'), stdio: 'inherit' });
      } catch (error) {
        console.error('❌ Build failed. Please fix build errors first.');
        process.exit(1);
      }
    }

    // Analyze JavaScript bundles
    await this.analyzeJSBundles(distPath);

    // Analyze CSS bundles
    await this.analyzeCSSBundles(distPath);

    // Generate recommendations
    this.generateRecommendations();

    // Print report
    this.printReport();

    return this.results;
  }

  async analyzeJSBundles(distPath) {
    const jsDir = path.join(distPath, 'static/js');

    if (!fs.existsSync(jsDir)) {
      console.log('⚠️ No JavaScript bundles found');
      return;
    }

    const files = fs.readdirSync(jsDir).filter(f => f.endsWith('.js'));

    for (const file of files) {
      const filePath = path.join(jsDir, file);
      const stats = fs.statSync(filePath);
      const sizeKB = (stats.size / 1024).toFixed(2);

      // Analyze content for dependency detection
      const content = fs.readFileSync(filePath, 'utf8');
      const dependencies = this.extractDependencies(content);

      this.results.bundles.push({
        type: 'javascript',
        name: file,
        sizeKB: parseFloat(sizeKB),
        sizeBytes: stats.size,
        dependencies
      });

      this.results.totalSize += stats.size;
    }
  }

  async analyzeCSSBundles(distPath) {
    const cssDir = path.join(distPath, 'static/css');

    if (!fs.existsSync(cssDir)) {
      console.log('⚠️ No CSS bundles found');
      return;
    }

    const files = fs.readdirSync(cssDir).filter(f => f.endsWith('.css'));

    for (const file of files) {
      const filePath = path.join(cssDir, file);
      const stats = fs.statSync(filePath);
      const sizeKB = (stats.size / 1024).toFixed(2);

      this.results.bundles.push({
        type: 'css',
        name: file,
        sizeKB: parseFloat(sizeKB),
        sizeBytes: stats.size
      });

      this.results.totalSize += stats.size;
    }
  }

  extractDependencies(content) {
    const dependencies = [];

    // Look for common import patterns
    const patterns = [
      /import\s+.*?\s+from\s+['"](.+?)['"]/g,
      /require\(['"](.+?)['"]\)/g
    ];

    patterns.forEach(pattern => {
      let match;
      while ((match = pattern.exec(content)) !== null) {
        const dep = match[1];
        if (!dep.startsWith('./') && !dep.startsWith('../')) {
          dependencies.push(dep);

          // Track dependency usage
          this.results.dependencies[dep] = (this.results.dependencies[dep] || 0) + 1;
        }
      }
    });

    return dependencies;
  }

  generateRecommendations() {
    const totalSizeMB = (this.results.totalSize / 1024 / 1024).toFixed(2);

    // Check total size
    if (this.results.totalSize > 1024 * 1024) {
      this.results.recommendations.push({
        type: 'critical',
        message: `Total bundle size is ${totalSizeMB}MB. Consider code splitting.`
      });
    }

    // Check individual bundles
    this.results.bundles.forEach(bundle => {
      if (bundle.sizeKB > 500) {
        this.results.recommendations.push({
          type: 'warning',
          message: `${bundle.name} is ${bundle.sizeKB}KB. Consider lazy loading.`
        });
      }
    });

    // Check for large dependencies
    Object.entries(this.results.dependencies).forEach(([dep, count]) => {
      if (count > 5) {
        this.results.recommendations.push({
          type: 'info',
          message: `${dep} is used in ${count} bundles. Consider deduplication.`
        });
      }
    });

    // Performance recommendations
    this.results.recommendations.push(
      {
        type: 'success',
        message: 'Enable gzip compression on your server to reduce transfer size by ~70%'
      },
      {
        type: 'success',
        message: 'Implement bundle caching with long-term cache headers'
      },
      {
        type: 'success',
        message: 'Consider using tree shaking to remove unused code'
      }
    );
  }

  printReport() {
    console.log('\n📊 Bundle Analysis Report');
    console.log('========================\n');

    // Total size
    const totalSizeMB = (this.results.totalSize / 1024 / 1024).toFixed(2);
    console.log(`📦 Total Bundle Size: ${totalSizeMB}MB\n`);

    // Individual bundles
    console.log('📁 Individual Bundles:');
    console.log('---------------------');

    this.results.bundles.forEach(bundle => {
      const icon = bundle.type === 'javascript' ? '🟨' : '🎨';
      const status = bundle.sizeKB > 500 ? '❌' : bundle.sizeKB > 250 ? '⚠️' : '✅';
      console.log(`${icon} ${status} ${bundle.name}: ${bundle.sizeKB}KB`);
    });

    // Dependencies
    if (Object.keys(this.results.dependencies).length > 0) {
      console.log('\n📦 Most Used Dependencies:');
      console.log('--------------------------');

      const sortedDeps = Object.entries(this.results.dependencies)
        .sort(([,a], [,b]) => b - a)
        .slice(0, 10);

      sortedDeps.forEach(([dep, count]) => {
        console.log(`📚 ${dep}: used in ${count} bundles`);
      });
    }

    // Recommendations
    console.log('\n💡 Recommendations:');
    console.log('-------------------');

    const typeIcons = {
      critical: '🚨',
      warning: '⚠️',
      info: 'ℹ️',
      success: '✅'
    };

    this.results.recommendations.forEach(rec => {
      const icon = typeIcons[rec.type] || '💡';
      console.log(`${icon} ${rec.message}`);
    });

    console.log('\n');
  }
}

// Run analysis if called directly
if (require.main === module) {
  const analyzer = new BundleAnalyzer();
  analyzer.analyze().catch(console.error);
}

module.exports = BundleAnalyzer;