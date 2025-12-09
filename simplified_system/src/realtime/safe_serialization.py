#!/usr/bin/env python3
"""
Safe Serialization Module - 安全序列化模塊
Provides secure alternatives to pickle for DataFrame and numpy array serialization
為DataFrame和numpy數組序列化提供安全替代方案
"""

import json
import numpy as np
import pandas as pd
import logging
from typing import Any, Dict, List, Union
from datetime import datetime

logger = logging.getLogger(__name__)

class SerializationError(Exception):
    """Base exception for serialization errors."""
    pass

class UnsupportedTypeError(SerializationError):
    """Raised when data type cannot be safely serialized."""
    pass

class DeserializationError(SerializationError):
    """Raised when data cannot be safely deserialized."""
    pass

class SafeDataSerializer:
    """Safe data serializer that avoids pickle vulnerabilities."""

    @staticmethod
    def serialize(data: Any) -> bytes:
        """Safely serialize data without security risks."""
        try:
            if isinstance(data, (dict, list, str, int, float, bool, type(None))):
                # Safe JSON serialization for simple types
                return json.dumps(data, default=str, separators=(',', ':')).encode('utf-8')
            elif isinstance(data, pd.DataFrame):
                # Safe DataFrame serialization
                return SafeDataSerializer._serialize_dataframe(data)
            elif isinstance(data, np.ndarray):
                # Safe numpy array serialization
                return SafeDataSerializer._serialize_ndarray(data)
            elif isinstance(data, datetime):
                # DateTime serialization
                return data.isoformat().encode('utf-8')
            else:
                raise UnsupportedTypeError(f"Unsupported data type: {type(data)}")

        except (TypeError, ValueError) as e:
            logger.error(f"Serialization error for {type(data)}: {e}")
            raise SerializationError(f"Cannot serialize data of type {type(data)}: {e}") from e

    @staticmethod
    def deserialize(data: bytes) -> Any:
        """Safely deserialize data without security risks."""
        try:
            # Try to parse as UTF-8 text first
            try:
                decoded_data = data.decode('utf-8')
            except UnicodeDecodeError:
                # Not text, continue to other methods
                decoded_data = None

            if decoded_data is not None:
                # Try JSON parsing
                try:
                    parsed = json.loads(decoded_data)

                    # Handle special serialized objects
                    if isinstance(parsed, dict) and '_type' in parsed:
                        return SafeDataSerializer._deserialize_special(parsed)

                    return parsed
                except json.JSONDecodeError:
                    # Not JSON, continue
                    pass

            # If we reach here, data is binary and not pickle
            raise DeserializationError("Cannot deserialize binary data - unknown format")

        except Exception as e:
            logger.error(f"Deserialization error: {e}")
            raise DeserializationError(f"Cannot deserialize data: {e}") from e

    @staticmethod
    def _serialize_dataframe(df: pd.DataFrame) -> bytes:
        """Safely serialize pandas DataFrame."""
        try:
            # Convert DataFrame to JSON-safe format with custom encoder
            def pandas_serializer(obj):
                if isinstance(obj, pd.Timestamp):
                    return obj.isoformat()
                elif hasattr(obj, '__iter__') and not isinstance(obj, (str, bytes)):
                    return list(obj)
                return str(obj)

            # Convert DataFrame to records with proper serialization
            data_records = []
            for record in df.to_dict('records'):
                serialized_record = {}
                for key, value in record.items():
                    if isinstance(value, pd.Timestamp):
                        serialized_record[key] = value.isoformat()
                    elif isinstance(value, (pd.Series, pd.DataFrame)):
                        serialized_record[key] = value.tolist()
                    else:
                        serialized_record[key] = value
                data_records.append(serialized_record)

            # Handle index serialization
            if isinstance(df.index, pd.DatetimeIndex):
                index_list = [ts.isoformat() for ts in df.index]
            else:
                index_list = df.index.tolist()

            dataframe_dict = {
                '_type': 'DataFrame',
                'data': data_records,
                'index': index_list,
                'columns': df.columns.tolist(),
                'dtypes': {col: str(dtype) for col, dtype in df.dtypes.items()}
            }
            return json.dumps(dataframe_dict, default=pandas_serializer).encode('utf-8')

        except Exception as e:
            logger.error(f"DataFrame serialization error: {e}")
            raise SerializationError(f"Cannot serialize DataFrame: {e}") from e

    @staticmethod
    def _serialize_ndarray(arr: np.ndarray) -> bytes:
        """Safely serialize numpy array."""
        try:
            # Convert numpy array to JSON-safe format
            array_dict = {
                '_type': 'ndarray',
                'data': arr.tolist(),
                'shape': arr.shape,
                'dtype': str(arr.dtype)
            }
            return json.dumps(array_dict).encode('utf-8')

        except Exception as e:
            logger.error(f"NumPy array serialization error: {e}")
            raise SerializationError(f"Cannot serialize numpy array: {e}") from e

    @staticmethod
    def _deserialize_special(data: Dict[str, Any]) -> Any:
        """Deserialize special object types."""
        try:
            obj_type = data.get('_type')

            if obj_type == 'DataFrame':
                return pd.DataFrame(
                    data['data'],
                    index=data['index'],
                    columns=data['columns']
                )
            elif obj_type == 'ndarray':
                return np.array(
                    data['data'],
                    dtype=data['dtype']
                ).reshape(data['shape'])
            else:
                raise DeserializationError(f"Unknown serialized type: {obj_type}")

        except Exception as e:
            logger.error(f"Special deserialization error for {data.get('_type')}: {e}")
            raise DeserializationError(f"Cannot deserialize special object: {e}") from e

# Test function to verify serialization works
def test_safe_serialization():
    """Test the safe serialization with various data types."""
    serializer = SafeDataSerializer()

    # Test simple types
    simple_data = {"symbol": "0700.HK", "price": 300.5, "volume": 15000}
    serialized = serializer.serialize(simple_data)
    deserialized = serializer.deserialize(serialized)
    assert deserialized == simple_data, "Simple type serialization failed"

    # Test DataFrame
    df = pd.DataFrame({
        'price': [300.1, 300.2, 300.3],
        'volume': [1000, 2000, 3000]
    })
    serialized_df = serializer.serialize(df)
    deserialized_df = serializer.deserialize(serialized_df)
    assert isinstance(deserialized_df, pd.DataFrame), "DataFrame deserialization failed"
    assert len(deserialized_df) == 3, "DataFrame row count mismatch"

    # Test numpy array
    arr = np.array([1, 2, 3, 4, 5])
    serialized_arr = serializer.serialize(arr)
    deserialized_arr = serializer.deserialize(serialized_arr)
    assert isinstance(deserialized_arr, np.ndarray), "NumPy array deserialization failed"
    assert np.array_equal(deserialized_arr, arr), "NumPy array data mismatch"

    print("✅ All safe serialization tests passed")

if __name__ == "__main__":
    test_safe_serialization()