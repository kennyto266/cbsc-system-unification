import React from 'react';
import { Row, Col, Card, Tabs } from 'antd';
import {
  HIBORDisplay,
  MonetaryBaseChart,
  SentimentGauge,
  PerformanceComparison,
  NonPriceDataProvider
} from './index';

/**
 * Integration Example for Non-Price Strategy Components
 *
 * This example shows how to integrate the non-price strategy components
 * into an existing dashboard or create a new section.
 */
const NonPriceIntegrationExample: React.FC = () => {
  return (
    <NonPriceDataProvider>
      <Card
        title="非價格策略分析"
        style={{ marginBottom: 16 }}
      >
        <Tabs
          defaultActiveKey="1"
          items={[
            {
              key: '1',
              label: '宏觀指標',
              children: (
                <Row gutter={[16, 16]}>
                  <Col xs={24} lg={12}>
                    <HIBORDisplay
                      timeframe="1M"
                      showRealTime={true}
                      height={300}
                    />
                  </Col>
                  <Col xs={24} lg={12}>
                    <MonetaryBaseChart
                      timeframe="3M"
                      showComparison={true}
                      height={300}
                    />
                  </Col>
                </Row>
              )
            },
            {
              key: '2',
              label: '市場情緒',
              children: (
                <Row gutter={[16, 16]}>
                  <Col xs={24} lg={8}>
                    <SentimentGauge
                      symbol="0700.HK"
                      showTrend={true}
                      showDetails={true}
                    />
                  </Col>
                  <Col xs={24} lg={8}>
                    <SentimentGauge
                      symbol="9988.HK"
                      showTrend={true}
                      showDetails={false}
                    />
                  </Col>
                  <Col xs={24} lg={8}>
                    <SentimentGauge
                      symbol="0941.HK"
                      showTrend={false}
                      showDetails={true}
                    />
                  </Col>
                </Row>
              )
            },
            {
              key: '3',
              label: '策略比較',
              children: (
                <Row gutter={[16, 16]}>
                  <Col span={24}>
                    <PerformanceComparison
                      defaultPeriod="3M"
                      showSettings={true}
                      height={400}
                    />
                  </Col>
                </Row>
              )
            }
          ]}
        />
      </Card>
    </NonPriceDataProvider>
  );
};

export default NonPriceIntegrationExample;

/**
 * Usage Instructions:
 *
 * 1. Import components:
 *    ```typescript
 *    import { HIBORDisplay, SentimentGauge } from '@/components/NonPrice';
 *    ```
 *
 * 2. Wrap your component with NonPriceDataProvider for context:
 *    ```typescript
 *    <NonPriceDataProvider>
 *      <YourComponent />
 *    </NonPriceDataProvider>
 *    ```
 *
 * 3. Use individual components with props:
 *    ```typescript
 *    <HIBORDisplay
 *      symbol="HIBOR"
 *      timeframe="1M"
 *      showRealTime={true}
 *    />
 *    ```
 *
 * 4. Access real-time data in custom components:
 *    ```typescript
 *    import { useNonPriceData } from '@/components/NonPrice';
 *
 *    const MyComponent = () => {
 *      const { signals, isConnected, subscribe } = useNonPriceData();
 *
 *      useEffect(() => {
 *        const unsubscribe = subscribe('0700.HK', (signal) => {
 *          console.log('New signal:', signal);
 *        });
 *
 *        return unsubscribe;
 *      }, []);
 *
 *      return <div>{/* Your JSX */}</div>;
 *    };
 *    ```
 */