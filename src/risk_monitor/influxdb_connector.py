"""
InfluxDB Connector for Time Series Data

This module handles data storage and retrieval from InfluxDB for risk monitoring:
- Portfolio and asset price data
- Risk metrics time series
- Historical performance data
- Alert history storage
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Optional, Union, Tuple
from datetime import datetime, timedelta
import logging
from influxdb_client import InfluxDBClient, Point
from influxdb_client.client.write_api import SYNCHRONOUS
from influxdb_client.client.query_api import QueryApi
import pytz

logger = logging.getLogger(__name__)


class InfluxDBConnector:
    """InfluxDB connector for risk monitoring data"""

    def __init__(
        self,
        host: str = "localhost",
        port: int = 8086,
        database: str = "risk_monitoring",
        username: str = "",
        password: str = "",
        token: str = "",
        org: str = "cbsc",
        bucket: str = "risk_data"
    ):
        """
        Initialize InfluxDB connector

        Args:
            host: InfluxDB host
            port: InfluxDB port
            database: Database name (legacy)
            username: Username
            password: Password
            token: Authentication token (InfluxDB 2.x)
            org: Organization name (InfluxDB 2.x)
            bucket: Bucket name (InfluxDB 2.x)
        """
        self.host = host
        self.port = port
        self.database = database
        self.username = username
        self.password = password
        self.token = token
        self.org = org
        self.bucket = bucket

        # Initialize client
        self._initialize_client()

    def _initialize_client(self):
        """Initialize InfluxDB client based on version"""
        try:
            # Try InfluxDB 2.x first
            if self.token:
                url = f"http://{self.host}:{self.port}"
                self.client = InfluxDBClient(
                    url=url,
                    token=self.token,
                    org=self.org
                )
                self.version = "2.x"
                logger.info("Connected to InfluxDB 2.x")
            else:
                raise ValueError("Token required for InfluxDB 2.x")
        except Exception as e:
            logger.warning(f"Failed to connect to InfluxDB 2.x: {e}")
            try:
                # Fallback to InfluxDB 1.x
                from influxdb import InfluxDBClient as InfluxDB1xClient
                self.client = InfluxDB1xClient(
                    host=self.host,
                    port=self.port,
                    username=self.username,
                    password=self.password,
                    database=self.database
                )
                self.version = "1.x"
                logger.info("Connected to InfluxDB 1.x")
            except Exception as e2:
                logger.error(f"Failed to connect to InfluxDB 1.x: {e2}")
                raise

        # Initialize write and query APIs
        if self.version == "2.x":
            self.write_api = self.client.write_api(write_options=SYNCHRONOUS)
            self.query_api = self.client.query_api()
        else:
            self.write_api = None
            self.query_api = None

    def write_portfolio_data(
        self,
        portfolio_id: str,
        timestamp: datetime,
        total_value: float,
        returns: Optional[float] = None,
        weights: Optional[Dict[str, float]] = None,
        metadata: Optional[Dict] = None
    ):
        """
        Write portfolio data to InfluxDB

        Args:
            portfolio_id: Portfolio identifier
            timestamp: Data timestamp
            total_value: Total portfolio value
            returns: Portfolio returns
            weights: Asset weights
            metadata: Additional metadata
        """
        if self.version == "2.x":
            point = Point("portfolio") \
                .tag("portfolio_id", portfolio_id) \
                .field("total_value", total_value) \
                .time(timestamp)

            if returns is not None:
                point = point.field("returns", returns)

            if weights:
                for asset, weight in weights.items():
                    point = point.field(f"weight_{asset}", weight)

            if metadata:
                for key, value in metadata.items():
                    if isinstance(value, (int, float)):
                        point = point.field(key, value)

            self.write_api.write(bucket=self.bucket, record=point)
        else:
            # InfluxDB 1.x format
            data_point = {
                "measurement": "portfolio",
                "tags": {"portfolio_id": portfolio_id},
                "fields": {"total_value": total_value},
                "time": timestamp
            }

            if returns is not None:
                data_point["fields"]["returns"] = returns

            if weights:
                for asset, weight in weights.items():
                    data_point["fields"][f"weight_{asset}"] = weight

            self.client.write_points([data_point])

    def write_asset_data(
        self,
        asset_id: str,
        timestamp: datetime,
        price: float,
        volume: Optional[float] = None,
        returns: Optional[float] = None,
        metadata: Optional[Dict] = None
    ):
        """
        Write asset price data to InfluxDB

        Args:
            asset_id: Asset identifier
            timestamp: Data timestamp
            price: Asset price
            volume: Trading volume
            returns: Asset returns
            metadata: Additional metadata
        """
        if self.version == "2.x":
            point = Point("asset") \
                .tag("asset_id", asset_id) \
                .field("price", price) \
                .time(timestamp)

            if volume is not None:
                point = point.field("volume", volume)

            if returns is not None:
                point = point.field("returns", returns)

            if metadata:
                for key, value in metadata.items():
                    if isinstance(value, (int, float)):
                        point = point.field(key, value)

            self.write_api.write(bucket=self.bucket, record=point)
        else:
            data_point = {
                "measurement": "asset",
                "tags": {"asset_id": asset_id},
                "fields": {"price": price},
                "time": timestamp
            }

            if volume is not None:
                data_point["fields"]["volume"] = volume

            if returns is not None:
                data_point["fields"]["returns"] = returns

            self.client.write_points([data_point])

    def write_risk_metrics(
        self,
        portfolio_id: str,
        timestamp: datetime,
        metrics: Dict[str, float],
        asset_id: Optional[str] = None
    ):
        """
        Write risk metrics to InfluxDB

        Args:
            portfolio_id: Portfolio identifier
            timestamp: Data timestamp
            metrics: Dictionary of risk metrics
            asset_id: Asset identifier (optional)
        """
        if self.version == "2.x":
            point = Point("risk_metrics") \
                .tag("portfolio_id", portfolio_id) \
                .time(timestamp)

            if asset_id:
                point = point.tag("asset_id", asset_id)

            for metric_name, value in metrics.items():
                point = point.field(metric_name, value)

            self.write_api.write(bucket=self.bucket, record=point)
        else:
            tags = {"portfolio_id": portfolio_id}
            if asset_id:
                tags["asset_id"] = asset_id

            data_point = {
                "measurement": "risk_metrics",
                "tags": tags,
                "fields": metrics,
                "time": timestamp
            }

            self.client.write_points([data_point])

    def write_alert_data(
        self,
        alert_id: str,
        timestamp: datetime,
        alert_data: Dict
    ):
        """
        Write alert data to InfluxDB

        Args:
            alert_id: Alert identifier
            timestamp: Alert timestamp
            alert_data: Alert information
        """
        if self.version == "2.x":
            point = Point("alerts") \
                .tag("alert_id", alert_id) \
                .tag("level", alert_data.get("level", "")) \
                .tag("type", alert_data.get("type", "")) \
                .time(timestamp)

            # Add fields
            for key, value in alert_data.items():
                if key not in ["level", "type"] and isinstance(value, (int, float)):
                    point = point.field(key, value)

            self.write_api.write(bucket=self.bucket, record=point)
        else:
            tags = {
                "alert_id": alert_id,
                "level": alert_data.get("level", ""),
                "type": alert_data.get("type", "")
            }

            fields = {k: v for k, v in alert_data.items()
                     if k not in ["level", "type"] and isinstance(v, (int, float))}

            data_point = {
                "measurement": "alerts",
                "tags": tags,
                "fields": fields,
                "time": timestamp
            }

            self.client.write_points([data_point])

    def query_portfolio_data(
        self,
        portfolio_id: str,
        start_time: datetime,
        end_time: Optional[datetime] = None,
        fields: Optional[List[str]] = None
    ) -> pd.DataFrame:
        """
        Query portfolio data

        Args:
            portfolio_id: Portfolio identifier
            start_time: Start time
            end_time: End time (optional)
            fields: Specific fields to query

        Returns:
            DataFrame with portfolio data
        """
        if end_time is None:
            end_time = datetime.now(pytz.UTC)

        if self.version == "2.x":
            # Build query
            field_selection = "_value"
            if fields:
                field_selection = ', '.join(fields)

            query = f'''
            from(bucket: "{self.bucket}")
                |> range(start: {start_time.isoformat()}, stop: {end_time.isoformat()})
                |> filter(fn: (r) => r._measurement == "portfolio")
                |> filter(fn: (r) => r.portfolio_id == "{portfolio_id}")
                |> pivot(rowKey:["_time"], columnKey: ["_field"], valueColumn: "_value")
            '''

            result = self.query_api.query_data_frame(query)
            if not result.empty:
                result = result.set_index('_time')
                result.index = pd.to_datetime(result.index)

            return result
        else:
            # InfluxDB 1.x query
            query = f'''
            SELECT {', '.join(fields) if fields else '*'}
            FROM portfolio
            WHERE portfolio_id = '{portfolio_id}'
            AND time >= '{start_time.isoformat()}'
            {'AND time <= \'' + end_time.isoformat() + '\'' if end_time else ''}
            '''

            result = self.client.query(query)
            points = list(result.get_points())

            if points:
                df = pd.DataFrame(points)
                df['time'] = pd.to_datetime(df['time'])
                df = df.set_index('time')
                return df
            else:
                return pd.DataFrame()

    def query_asset_data(
        self,
        asset_id: str,
        start_time: datetime,
        end_time: Optional[datetime] = None,
        fields: Optional[List[str]] = None
    ) -> pd.DataFrame:
        """
        Query asset data

        Args:
            asset_id: Asset identifier
            start_time: Start time
            end_time: End time (optional)
            fields: Specific fields to query

        Returns:
            DataFrame with asset data
        """
        if end_time is None:
            end_time = datetime.now(pytz.UTC)

        if self.version == "2.x":
            field_selection = "_value"
            if fields:
                field_selection = ', '.join(fields)

            query = f'''
            from(bucket: "{self.bucket}")
                |> range(start: {start_time.isoformat()}, stop: {end_time.isoformat()})
                |> filter(fn: (r) => r._measurement == "asset")
                |> filter(fn: (r) => r.asset_id == "{asset_id}")
                |> pivot(rowKey:["_time"], columnKey: ["_field"], valueColumn: "_value")
            '''

            result = self.query_api.query_data_frame(query)
            if not result.empty:
                result = result.set_index('_time')
                result.index = pd.to_datetime(result.index)

            return result
        else:
            query = f'''
            SELECT {', '.join(fields) if fields else '*'}
            FROM asset
            WHERE asset_id = '{asset_id}'
            AND time >= '{start_time.isoformat()}'
            {'AND time <= \'' + end_time.isoformat() + '\'' if end_time else ''}
            '''

            result = self.client.query(query)
            points = list(result.get_points())

            if points:
                df = pd.DataFrame(points)
                df['time'] = pd.to_datetime(df['time'])
                df = df.set_index('time')
                return df
            else:
                return pd.DataFrame()

    def query_risk_metrics(
        self,
        portfolio_id: str,
        start_time: datetime,
        end_time: Optional[datetime] = None,
        asset_id: Optional[str] = None,
        metrics: Optional[List[str]] = None
    ) -> pd.DataFrame:
        """
        Query risk metrics

        Args:
            portfolio_id: Portfolio identifier
            start_time: Start time
            end_time: End time (optional)
            asset_id: Asset identifier (optional)
            metrics: Specific metrics to query

        Returns:
            DataFrame with risk metrics
        """
        if end_time is None:
            end_time = datetime.now(pytz.UTC)

        if self.version == "2.x":
            query = f'''
            from(bucket: "{self.bucket}")
                |> range(start: {start_time.isoformat()}, stop: {end_time.isoformat()})
                |> filter(fn: (r) => r._measurement == "risk_metrics")
                |> filter(fn: (r) => r.portfolio_id == "{portfolio_id}")
            '''

            if asset_id:
                query += f'|> filter(fn: (r) => r.asset_id == "{asset_id}")'

            if metrics:
                metric_filter = ' or '.join([f'r._field == "{metric}"' for metric in metrics])
                query += f'|> filter(fn: (r) => {metric_filter})'

            query += '|> pivot(rowKey:["_time"], columnKey: ["_field"], valueColumn: "_value")'

            result = self.query_api.query_data_frame(query)
            if not result.empty:
                result = result.set_index('_time')
                result.index = pd.to_datetime(result.index)

            return result
        else:
            where_conditions = [
                f"portfolio_id = '{portfolio_id}'",
                f"time >= '{start_time.isoformat()}'"
            ]

            if asset_id:
                where_conditions.append(f"asset_id = '{asset_id}'")

            if end_time:
                where_conditions.append(f"time <= '{end_time.isoformat()}'")

            query = f'''
            SELECT {', '.join(metrics) if metrics else '*'}
            FROM risk_metrics
            WHERE {' AND '.join(where_conditions)}
            '''

            result = self.client.query(query)
            points = list(result.get_points())

            if points:
                df = pd.DataFrame(points)
                df['time'] = pd.to_datetime(df['time'])
                df = df.set_index('time')
                return df
            else:
                return pd.DataFrame()

    def query_latest_portfolio_value(
        self,
        portfolio_id: str
    ) -> Optional[float]:
        """
        Query latest portfolio value

        Args:
            portfolio_id: Portfolio identifier

        Returns:
            Latest portfolio value or None
        """
        if self.version == "2.x":
            query = f'''
            from(bucket: "{self.bucket}")
                |> range(start: -30d)
                |> filter(fn: (r) => r._measurement == "portfolio")
                |> filter(fn: (r) => r.portfolio_id == "{portfolio_id}")
                |> filter(fn: (r) => r._field == "total_value")
                |> last()
            '''

            result = self.query_api.query_data_frame(query)
            if not result.empty:
                return result['_value'].iloc[0]
            return None
        else:
            query = f'''
            SELECT last(total_value)
            FROM portfolio
            WHERE portfolio_id = '{portfolio_id}'
            '''

            result = self.client.query(query)
            points = list(result.get_points())

            if points:
                return points[0]['last']
            return None

    def batch_write_data_points(
        self,
        data_points: List[Dict],
        measurement: str
    ):
        """
        Batch write multiple data points

        Args:
            data_points: List of data point dictionaries
            measurement: Measurement name
        """
        if self.version == "2.x":
            points = []
            for dp in data_points:
                point = Point(measurement).time(dp['time'])

                # Add tags
                for tag_key, tag_value in dp.get('tags', {}).items():
                    point = point.tag(tag_key, tag_value)

                # Add fields
                for field_key, field_value in dp.get('fields', {}).items():
                    if isinstance(field_value, (int, float)):
                        point = point.field(field_key, field_value)

                points.append(point)

            self.write_api.write(bucket=self.bucket, record=points)
        else:
            influx_points = []
            for dp in data_points:
                influx_points.append({
                    "measurement": measurement,
                    "tags": dp.get('tags', {}),
                    "fields": dp.get('fields', {}),
                    "time": dp['time']
                })

            self.client.write_points(influx_points)

    def delete_data(
        self,
        measurement: str,
        start_time: datetime,
        end_time: datetime,
        tags: Optional[Dict] = None
    ):
        """
        Delete data from InfluxDB

        Args:
            measurement: Measurement name
            start_time: Start time
            end_time: End time
            tags: Tags to filter by
        """
        if self.version == "2.x":
            # Build delete predicate
            predicate = f'_measurement="{measurement}"'

            if tags:
                for tag_key, tag_value in tags.items():
                    predicate += f' AND {tag_key}="{tag_value}"'

            self.client.delete_api().delete(
                start=start_time,
                stop=end_time,
                predicate=predicate,
                bucket=self.bucket,
                org=self.org
            )
        else:
            logger.warning("Delete not implemented for InfluxDB 1.x")

    def close(self):
        """Close InfluxDB connection"""
        if self.client:
            self.client.close()
            logger.info("InfluxDB connection closed")