/**
 * Frontend Load Testing
 * Simulates high user traffic and concurrent interactions
 */

const puppeteer = require('puppeteer')
const { performance } = require('perf_hooks')

class FrontendLoadTest {
  constructor() {
    this.metrics = {
      pageLoadTimes: [],
      interactionTimes: [],
      errors: [],
      concurrentUsers: 0
    }
  }

  async measurePageLoadTime(page, url) {
    const startTime = performance.now()

    await page.goto(url, {
      waitUntil: 'networkidle2',
      timeout: 30000
    })

    // Wait for main content to be ready
    await page.waitForSelector('[data-testid="dashboard-content"]')

    const endTime = performance.now()
    const loadTime = endTime - startTime

    // Get performance metrics from browser
    const performanceMetrics = await page.evaluate(() => {
      const navigation = performance.getEntriesByType('navigation')[0]
      return {
        domContentLoaded: navigation.domContentLoadedEventEnd - navigation.domContentLoadedEventStart,
        loadComplete: navigation.loadEventEnd - navigation.loadEventStart,
        firstPaint: performance.getEntriesByName('first-paint')[0]?.startTime || 0,
        firstContentfulPaint: performance.getEntriesByName('first-contentful-paint')[0]?.startTime || 0
      }
    })

    return {
      totalTime: loadTime,
      ...performanceMetrics
    }
  }

  async simulateUserInteraction(page, interactions = []) {
    const interactionTimes = []

    for (const interaction of interactions) {
      const startTime = performance.now()

      try {
        switch (interaction.type) {
          case 'click':
            await page.click(interaction.selector)
            break
          case 'type':
            await page.type(interaction.selector, interaction.text)
            break
          case 'navigate':
            await page.click(interaction.selector)
            await page.waitForSelector('[data-testid="loading"]', { hidden: true })
            break
          case 'scroll':
            await page.evaluate((selector) => {
              document.querySelector(selector)?.scrollIntoView()
            }, interaction.selector)
            break
        }

        const endTime = performance.now()
        interactionTimes.push(endTime - startTime)

        // Add small delay between interactions
        await page.sleep(100)

      } catch (error) {
        this.metrics.errors.push({
          interaction,
          error: error.message,
          timestamp: new Date().toISOString()
        })
      }
    }

    return interactionTimes
  }

  async simulateUserFlow(userId) {
    const browser = await puppeteer.launch({
      headless: true,
      args: ['--no-sandbox', '--disable-setuid-sandbox']
    })
    const page = await browser.newPage()

    // Set viewport to common resolution
    await page.setViewport({ width: 1920, height: 1080 })

    try {
      console.log(`Starting user flow for user ${userId}`)

      // Step 1: Login
      const loginMetrics = await this.measurePageLoadTime(page, 'http://localhost:3000/login')
      await page.type('#username', `testuser${userId}`)
      await page.type('#password', 'testpassword')
      await page.click('#login-button')
      await page.waitForNavigation()

      // Step 2: Navigate to dashboard
      const dashboardMetrics = await this.measurePageLoadTime(page, 'http://localhost:3000/dashboard')

      // Step 3: Navigate to strategies
      const strategiesMetrics = await this.measurePageLoadTime(page, 'http://localhost:3000/strategies')

      // Step 4: Interact with strategies list
      const strategyInteractions = [
        { type: 'scroll', selector: '[data-testid="strategies-list"]' },
        { type: 'click', selector: '[data-testid="strategy-filter"]' },
        { type: 'type', selector: '[data-testid="search-input"]', text: 'MA' }
      ]

      const interactionTimes = await this.simulateUserInteraction(page, strategyInteractions)

      // Step 5: Create new strategy
      await page.click('[data-testid="create-strategy-btn"]')
      await page.waitForSelector('[data-testid="strategy-form"]')

      const createInteractions = [
        { type: 'type', selector: '[data-testid="strategy-name"]', text: `Test Strategy ${userId}` },
        { type: 'type', selector: '[data-testid="strategy-description"]', text: 'Load test strategy' },
        { type: 'click', selector: '[data-testid="save-strategy-btn"]' }
      ]

      const createTimes = await this.simulateUserInteraction(page, createInteractions)

      // Step 6: View performance analysis
      const performanceMetrics = await this.measurePageLoadTime(page, 'http://localhost:3000/strategies/1/performance')

      // Collect all metrics
      this.metrics.pageLoadTimes.push({
        userId,
        login: loginMetrics,
        dashboard: dashboardMetrics,
        strategies: strategiesMetrics,
        performance: performanceMetrics
      })

      this.metrics.interactionTimes.push({
        userId,
        interactions: [...interactionTimes, ...createTimes]
      })

    } catch (error) {
      this.metrics.errors.push({
        userId,
        error: error.message,
        timestamp: new Date().toISOString()
      })
    } finally {
      await browser.close()
    }
  }

  async runConcurrentUsersTest(userCount = 10) {
    console.log(`Starting load test with ${userCount} concurrent users`)
    const startTime = performance.now()

    // Create user promises
    const userPromises = []
    for (let i = 1; i <= userCount; i++) {
      userPromises.push(this.simulateUserFlow(i))
    }

    // Wait for all users to complete
    await Promise.all(userPromises)

    const totalTime = performance.now() - startTime
    console.log(`Load test completed in ${totalTime.toFixed(2)}ms`)

    return this.generateReport()
  }

  async runStressTest(duration = 60000) { // 60 seconds
    console.log(`Starting stress test for ${duration}ms`)

    const startTime = performance.now()
    let userId = 1

    while (performance.now() - startTime < duration) {
      this.simulateUserFlow(userId++)
      this.metrics.concurrentUsers++

      // Small delay between user starts
      await new Promise(resolve => setTimeout(resolve, 100))
    }

    return this.generateReport()
  }

  generateReport() {
    const avgPageLoadTime = this.calculateAverage(
      this.metrics.pageLoadTimes.flatMap(p =>
        Object.values(p).filter(m => typeof m === 'object' && m.totalTime).map(m => m.totalTime)
      )
    )

    const avgInteractionTime = this.calculateAverage(
      this.metrics.interactionTimes.flatMap(i => i.interactions)
    )

    const errorRate = (this.metrics.errors.length / this.metrics.concurrentUsers) * 100

    return {
      summary: {
        totalUsers: this.metrics.concurrentUsers,
        averagePageLoadTime: avgPageLoadTime.toFixed(2),
        averageInteractionTime: avgInteractionTime.toFixed(2),
        errorRate: errorRate.toFixed(2),
        totalErrors: this.metrics.errors.length
      },
      detailed: {
        pageLoadTimes: this.metrics.pageLoadTimes,
        interactionTimes: this.metrics.interactionTimes,
        errors: this.metrics.errors
      },
      recommendations: this.generateRecommendations(avgPageLoadTime, avgInteractionTime, errorRate)
    }
  }

  calculateAverage(values) {
    if (values.length === 0) return 0
    return values.reduce((sum, val) => sum + val, 0) / values.length
  }

  generateRecommendations(avgPageLoadTime, avgInteractionTime, errorRate) {
    const recommendations = []

    if (avgPageLoadTime > 3000) {
      recommendations.push('Page load times are high. Consider optimizing bundle size and server response times.')
    }

    if (avgInteractionTime > 500) {
      recommendations.push('Interaction times are slow. Review component rendering efficiency and debouncing.')
    }

    if (errorRate > 5) {
      recommendations.push('High error rate detected. Review error handling and retry mechanisms.')
    }

    if (recommendations.length === 0) {
      recommendations.push('Performance metrics are within acceptable ranges.')
    }

    return recommendations
  }
}

// Run tests if called directly
if (require.main === module) {
  const loadTest = new FrontendLoadTest()

  async function runTests() {
    try {
      console.log('=== Frontend Load Testing ===\n')

      // Concurrent users test
      console.log('1. Concurrent Users Test (10 users)')
      const concurrentResults = await loadTest.runConcurrentUsersTest(10)
      console.log(JSON.stringify(concurrentResults.summary, null, 2))
      console.log()

      // Reset metrics for stress test
      loadTest.metrics = {
        pageLoadTimes: [],
        interactionTimes: [],
        errors: [],
        concurrentUsers: 0
      }

      // Stress test (shorter duration for demo)
      console.log('2. Stress Test (30 seconds)')
      const stressResults = await loadTest.runStressTest(30000)
      console.log(JSON.stringify(stressResults.summary, null, 2))
      console.log()

      console.log('=== Load Testing Complete ===')

    } catch (error) {
      console.error('Load testing failed:', error)
      process.exit(1)
    }
  }

  runTests()
}

module.exports = FrontendLoadTest