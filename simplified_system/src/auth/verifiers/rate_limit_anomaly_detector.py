#!/usr / bin / env python3
"""
Rate Limit Anomaly Detector
速率限制异常检测器

Task 10: Deploy Rate Limit Anomaly Detection with adaptive thresholds
任务10：部署速率限制异常检测，支持自适应阈值

Provides request pattern analysis using sliding windows, adaptive rate limiting
based on endpoint capacity, and graduated response system.
"""

import asyncio
import json
import logging
import time
from collections import defaultdict, deque
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

from ..interfaces.auth_result import AuthResult, Verdict
from ..interfaces.verifier_interface import IVerifier

logger = logging.getLogger(__name__)


class RateLimitAnomalyDetector(IVerifier):
    """
    Rate Limit Anomaly Detector for API request pattern analysis
    速率限制异常检测器，用于API请求模式分析

    Features:
    - Request pattern analysis using sliding windows
    - Adaptive rate limiting based on endpoint capacity
    - Graduated response system (warning → throttle → block)
    - Integration with existing alert system
    """

    def __init__(
        self,
        name: str = "Rate Limit Anomaly Detector",
        config: Optional[Dict[str, Any]] = None,
    ):
        super().__init__(name, config)

        # Sliding window configuration
        self.window_sizes = self.config.get(
            "window_sizes", [60, 300, 900]
        )  # 1min, 5min, 15min
        self.max_requests_per_window = self.config.get(
            "max_requests_per_window",
            {
                60: 100,  # 100 requests per minute
                300: 400,  # 400 requests per 5 minutes
                900: 1000,  # 1000 requests per 15 minutes
            },
        )

        # Adaptive thresholds
        self.enable_adaptive_thresholds = self.config.get(
            "enable_adaptive_thresholds", True
        )
        self.adaptive_factor = self.config.get("adaptive_factor", 0.2)  # 20% adjustment
        self.min_threshold = self.config.get("min_threshold", 10)
        self.max_threshold = self.config.get("max_threshold", 10000)

        # Response levels
        self.response_levels = {
            "warning": {
                "threshold": 0.7,  # 70% of limit
                "action": "log_warning",
                "delay_ms": 0,
            },
            "throttle": {
                "threshold": 0.85,  # 85% of limit
                "action": "add_delay",
                "delay_ms": 1000,  # 1 second delay
            },
            "block": {
                "threshold": 1.0,  # 100% of limit
                "action": "block_request",
                "delay_ms": 0,
            },
        }

        # Storage for request tracking
        self.request_windows = defaultdict(
            lambda: defaultdict(deque)
        )  # endpoint -> window_size -> deque
        self.blocked_endpoints = defaultdict(dict)  # endpoint -> block_info
        self.endpoint_statistics = defaultdict(dict)  # endpoint -> stats

        # Configuration
        self.cleanup_interval = self.config.get("cleanup_interval", 300)  # 5 minutes
        self.block_duration = self.config.get("block_duration", 300)  # 5 minutes
        self.statistics_file = self.config.get(
            "statistics_file", "config / rate_limit_stats.json"
        )

        # Load existing statistics
        self._load_statistics()

        # Start background cleanup task
        self._cleanup_task = None
        self._start_cleanup_task()

        logger.info(
            f"Rate Limit Anomaly Detector initialized with windows: {self.window_sizes}"
        )

    def _load_statistics(self):
        """Load endpoint statistics from file"""
        try:
            stats_file = Path(self.statistics_file)
            if stats_file.exists():
                with open(stats_file, "r", encoding="utf - 8") as f:
                    self.endpoint_statistics = json.load(f)

                # Convert string keys back to appropriate types
                self.endpoint_statistics = {
                    k: {
                        "requests_per_window": {
                            int(w): (
                                v["requests_per_window"][w]
                                if isinstance(v["requests_per_window"], dict)
                                else v.get("requests_per_window", {})
                            )
                            for w in self.window_sizes
                        },
                        "adaptive_thresholds": v.get("adaptive_thresholds", {}),
                        "last_updated": v.get(
                            "last_updated", datetime.utcnow().isoformat()
                        ),
                    }
                    for k, v in self.endpoint_statistics.items()
                }

        except Exception as e:
            logger.error(f"Failed to load rate limit statistics: {e}")
            self.endpoint_statistics = defaultdict(dict)

    def _save_statistics(self):
        """Save endpoint statistics to file"""
        try:
            stats_file = Path(self.statistics_file)
            stats_file.parent.mkdir(parents = True, exist_ok = True)

            with open(stats_file, "w", encoding="utf - 8") as f:
                json.dump(self.endpoint_statistics, f, indent = 2, ensure_ascii = False)

        except Exception as e:
            logger.error(f"Failed to save rate limit statistics: {e}")

    def _start_cleanup_task(self):
        """Start background cleanup task"""
        if self._cleanup_task is None:
            self._cleanup_task = asyncio.create_task(self._background_cleanup())

    async def _background_cleanup(self):
        """Background task to clean up old request data"""
        while True:
            try:
                await asyncio.sleep(self.cleanup_interval)
                await self._cleanup_old_requests()
                self._save_statistics()
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Background cleanup error: {e}")

    async def _cleanup_old_requests(self):
        """Clean up old request data from sliding windows"""
        current_time = time.time()

        for endpoint in list(self.request_windows.keys()):
            for window_size in self.window_sizes:
                window = self.request_windows[endpoint][window_size]
                cutoff_time = current_time - window_size

                # Remove old requests from window
                while window and window[0] < cutoff_time:
                    window.popleft()

            # Remove empty windows
            for window_size in self.window_sizes:
                if not self.request_windows[endpoint][window_size]:
                    del self.request_windows[endpoint][window_size]

            # Remove endpoint if no windows left
            if not self.request_windows[endpoint]:
                del self.request_windows[endpoint]

        # Clean up expired blocks
        for endpoint in list(self.blocked_endpoints.keys()):
            block_info = self.blocked_endpoints[endpoint]
            if current_time > block_info.get("blocked_until", 0):
                del self.blocked_endpoints[endpoint]
                logger.info(f"Block expired for endpoint: {endpoint}")

    async def verify(
        self, data: Any, data_id: str, context: Optional[Dict[str, Any]] = None
    ) -> AuthResult:
        """
        Verify request rate limits and detect anomalies

        Args:
            data: Request data (endpoint info, request metadata)
            data_id: Unique data identifier (usually request ID)
            context: Verification context (timestamp, user info, etc.)

        Returns:
            AuthResult: Verification result
        """
        start_time = time.time()

        result = AuthResult(
            data_id = data_id,
            overall_verdict = Verdict.UNKNOWN,
            overall_confidence = 0.0,
            metadata={
                "algorithm": "rate_limit_anomaly_detection",
                "verifier": self.name,
            },
        )

        try:
            # Extract request information
            request_info = self._extract_request_info(data, context)

            if not request_info.get("endpoint"):
                result.overall_verdict = Verdict.SUSPICIOUS
                result.overall_confidence = 0.3
                result.error_message = "No endpoint information provided"
                return result

            endpoint = request_info["endpoint"]
            current_time = request_info.get("timestamp", time.time())

            # Check if endpoint is currently blocked
            if endpoint in self.blocked_endpoints:
                block_info = self.blocked_endpoints[endpoint]
                if current_time < block_info["blocked_until"]:
                    result.overall_verdict = Verdict.FALSIFIED
                    result.overall_confidence = 0.95
                    result.error_message = f"Endpoint blocked due to rate limit violations. Block expires: {datetime.fromtimestamp(block_info['blocked_until'])}"
                    result.metadata.update(
                        {
                            "action": "blocked",
                            "block_reason": block_info["reason"],
                            "block_expires": block_info["blocked_until"],
                        }
                    )
                    return result
                else:
                    # Block expired, remove it
                    del self.blocked_endpoints[endpoint]

            # Record the request
            await self._record_request(endpoint, current_time)

            # Analyze request patterns
            analysis_result = await self._analyze_request_patterns(
                endpoint, current_time
            )
            result.overall_verdict = analysis_result["verdict"]
            result.overall_confidence = analysis_result["confidence"]
            result.metadata.update(analysis_result["metadata"])

            # Apply graduated response
            response_action = analysis_result.get("response_action")
            if response_action:
                if response_action["action"] == "add_delay":
                    await asyncio.sleep(response_action["delay_ms"] / 1000.0)
                    result.metadata["delay_applied_ms"] = response_action["delay_ms"]

                elif response_action["action"] == "block_request":
                    # Block the endpoint
                    self._block_endpoint(
                        endpoint,
                        analysis_result.get("block_reason", "Rate limit exceeded"),
                    )
                    result.overall_verdict = Verdict.FALSIFIED
                    result.overall_confidence = 0.9
                    result.error_message = "Request blocked due to rate limit violation"

            # Update endpoint statistics
            await self._update_endpoint_statistics(endpoint, analysis_result)

            logger.info(
                f"Rate limit analysis completed for {endpoint}: {result.overall_verdict.value}"
            )

        except Exception as e:
            result.overall_verdict = Verdict.ERROR
            result.error_message = f"Rate limit analysis failed: {str(e)}"
            logger.error(f"Rate limit analysis error for {data_id}: {e}")

        finally:
            result.total_execution_time_ms = (time.time() - start_time) * 1000

        return result

    def _extract_request_info(
        self, data: Any, context: Optional[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Extract request information from data and context"""
        request_info = {}

        # Handle request data as dict
        if isinstance(data, dict):
            request_info.update(data)

        # Add context information
        if context:
            request_info.update(context)

        # Ensure timestamp
        if "timestamp" not in request_info:
            request_info["timestamp"] = time.time()

        return request_info

    async def _record_request(self, endpoint: str, timestamp: float):
        """Record a request in sliding windows"""
        for window_size in self.window_sizes:
            self.request_windows[endpoint][window_size].append(timestamp)

    async def _analyze_request_patterns(
        self, endpoint: str, current_time: float
    ) -> Dict[str, Any]:
        """Analyze request patterns for anomalies"""
        try:
            analysis_metadata = {
                "endpoint": endpoint,
                "window_analysis": {},
                "anomaly_detected": False,
            }

            max_utilization = 0.0
            response_action = None
            overall_verdict = Verdict.AUTHENTIC
            confidence = 0.8

            # Analyze each window size
            for window_size in self.window_sizes:
                window = self.request_windows[endpoint][window_size]
                request_count = len(window)

                # Get adaptive threshold for this endpoint
                threshold = self._get_adaptive_threshold(endpoint, window_size)
                utilization = request_count / threshold if threshold > 0 else 0

                max_utilization = max(max_utilization, utilization)

                analysis_metadata["window_analysis"][window_size] = {
                    "request_count": request_count,
                    "threshold": threshold,
                    "utilization": utilization,
                    "time_window": f"{window_size}s",
                }

                # Check if utilization exceeds thresholds
                for level_name, level_config in self.response_levels.items():
                    if utilization >= level_config["threshold"]:
                        if level_name == "warning":
                            analysis_metadata["anomaly_detected"] = True
                            overall_verdict = Verdict.SUSPICIOUS
                            confidence = max(confidence, 0.6)

                        elif level_name == "throttle":
                            analysis_metadata["anomaly_detected"] = True
                            response_action = {
                                "action": level_config["action"],
                                "delay_ms": level_config["delay_ms"],
                                "reason": f"High request rate: {utilization:.1%} of limit in {window_size}s window",
                            }
                            overall_verdict = Verdict.SUSPICIOUS
                            confidence = max(confidence, 0.7)

                        elif level_name == "block":
                            analysis_metadata["anomaly_detected"] = True
                            response_action = {
                                "action": level_config["action"],
                                "reason": f"Rate limit exceeded: {utilization:.1%} of limit in {window_size}s window",
                            }
                            overall_verdict = Verdict.FALSIFIED
                            confidence = 0.9

            # Detect unusual patterns (bursts, gaps)
            pattern_analysis = self._detect_unusual_patterns(endpoint, current_time)
            analysis_metadata["pattern_analysis"] = pattern_analysis

            if pattern_analysis.get("unusual_pattern_detected", False):
                analysis_metadata["anomaly_detected"] = True
                confidence = max(confidence, 0.8)
                if overall_verdict == Verdict.AUTHENTIC:
                    overall_verdict = Verdict.SUSPICIOUS

            return {
                "verdict": overall_verdict,
                "confidence": confidence,
                "metadata": analysis_metadata,
                "response_action": response_action,
                "max_utilization": max_utilization,
            }

        except Exception as e:
            return {
                "verdict": Verdict.ERROR,
                "confidence": 0.0,
                "metadata": {"error": f"Pattern analysis error: {str(e)}"},
            }

    def _get_adaptive_threshold(self, endpoint: str, window_size: int) -> int:
        """Get adaptive threshold for endpoint"""
        base_threshold = self.max_requests_per_window.get(window_size, 100)

        if not self.enable_adaptive_thresholds:
            return base_threshold

        # Get endpoint statistics for adaptive adjustment
        endpoint_stats = self.endpoint_statistics.get(endpoint, {})
        adaptive_thresholds = endpoint_stats.get("adaptive_thresholds", {})
        stored_threshold = adaptive_thresholds.get(str(window_size))

        if stored_threshold:
            return stored_threshold

        # Calculate adaptive threshold based on historical usage
        if endpoint in self.request_windows:
            window = self.request_windows[endpoint][window_size]
            avg_usage = len(window)

            # Adjust threshold based on usage pattern
            if avg_usage > 0:
                adjustment = min(self.adaptive_factor, avg_usage / base_threshold)
                adaptive_threshold = int(base_threshold * (1 + adjustment))
                adaptive_threshold = max(
                    self.min_threshold, min(self.max_threshold, adaptive_threshold)
                )
                return adaptive_threshold

        return base_threshold

    def _detect_unusual_patterns(
        self, endpoint: str, current_time: float
    ) -> Dict[str, Any]:
        """Detect unusual request patterns (bursts, gaps)"""
        try:
            pattern_info = {"unusual_pattern_detected": False, "patterns_detected": []}

            # Check for burst patterns (many requests in short time)
            if endpoint in self.request_windows:
                # Check smallest window (60 seconds) for bursts
                window = self.request_windows[endpoint][60]
                if len(window) > 10:  # More than 10 requests in 1 minute
                    # Calculate inter - request times
                    if len(window) > 1:
                        intervals = [
                            window[i + 1] - window[i] for i in range(len(window) - 1)
                        ]
                        avg_interval = sum(intervals) / len(intervals)

                        # If average interval is less than 1 second, it's a burst
                        if avg_interval < 1.0:
                            pattern_info["unusual_pattern_detected"] = True
                            pattern_info["patterns_detected"].append(
                                {
                                    "type": "burst",
                                    "description": f"High - frequency requests detected (avg interval: {avg_interval:.2f}s)",
                                    "request_count": len(window),
                                }
                            )

            # Check for unusual timing patterns
            # This could be extended to detect DoS patterns, timing attacks, etc.

            return pattern_info

        except Exception as e:
            return {
                "unusual_pattern_detected": False,
                "error": f"Pattern detection error: {str(e)}",
            }

    def _block_endpoint(self, endpoint: str, reason: str):
        """Block an endpoint temporarily"""
        current_time = time.time()
        blocked_until = current_time + self.block_duration

        self.blocked_endpoints[endpoint] = {
            "blocked_at": current_time,
            "blocked_until": blocked_until,
            "reason": reason,
            "block_duration": self.block_duration,
        }

        logger.warning(
            f"Endpoint blocked: {endpoint} - Reason: {reason} - Duration: {self.block_duration}s"
        )

    async def _update_endpoint_statistics(
        self, endpoint: str, analysis_result: Dict[str, Any]
    ):
        """Update endpoint statistics for adaptive thresholds"""
        try:
            if endpoint not in self.endpoint_statistics:
                self.endpoint_statistics[endpoint] = {
                    "requests_per_window": {},
                    "adaptive_thresholds": {},
                    "last_updated": datetime.utcnow().isoformat(),
                }

            stats = self.endpoint_statistics[endpoint]

            # Update request counts per window
            window_analysis = analysis_result["metadata"].get("window_analysis", {})
            for window_size in self.window_sizes:
                if str(window_size) in window_analysis:
                    request_count = window_analysis[str(window_size)]["request_count"]
                    stats["requests_per_window"][str(window_size)] = request_count

            # Update adaptive thresholds if enabled
            if self.enable_adaptive_thresholds:
                for window_size in self.window_sizes:
                    current_threshold = self._get_adaptive_threshold(
                        endpoint, window_size
                    )
                    stats["adaptive_thresholds"][str(window_size)] = current_threshold

            stats["last_updated"] = datetime.utcnow().isoformat()

        except Exception as e:
            logger.error(f"Failed to update endpoint statistics: {e}")

    def get_verifier_type(self) -> str:
        """Get verifier type identifier"""
        return "rate_limit_anomaly_detection"

    def get_supported_data_types(self) -> List[str]:
        """Get supported data types"""
        return [
            "api_request",
            "endpoint_request",
            "request_metadata",
            "connection_info",
        ]

    async def health_check(self) -> Dict[str, Any]:
        """Health check for the rate limit anomaly detector"""
        health_status = {
            "verifier": self.name,
            "type": self.get_verifier_type(),
            "enabled": self.enabled,
            "status": "healthy",
            "tracked_endpoints": len(self.request_windows),
            "blocked_endpoints": len(self.blocked_endpoints),
            "window_sizes": self.window_sizes,
            "cleanup_task_running": self._cleanup_task is not None
            and not self._cleanup_task.done(),
        }

        # Test with sample data
        try:
            test_endpoint = "health_check_test"
            test_time = time.time()

            # Record test request
            await self._record_request(test_endpoint, test_time)

            # Analyze patterns
            analysis_result = await self._analyze_request_patterns(
                test_endpoint, test_time
            )

            if analysis_result["verdict"] in [Verdict.AUTHENTIC, Verdict.SUSPICIOUS]:
                health_status["pattern_analysis_test"] = "passed"
            else:
                health_status["pattern_analysis_test"] = f"failed: unexpected verdict"

            # Clean up test data
            if test_endpoint in self.request_windows:
                del self.request_windows[test_endpoint]

        except Exception as e:
            health_status["pattern_analysis_test"] = f"failed: {str(e)}"
            health_status["status"] = "unhealthy"

        return health_status

    async def cleanup(self):
        """Cleanup resources"""
        logger.info(f"Cleaning up {self.name}")

        # Cancel background task
        if self._cleanup_task:
            self._cleanup_task.cancel()
            try:
                await self._cleanup_task
            except asyncio.CancelledError:
                pass

        # Save statistics
        self._save_statistics()

        # Clear data structures
        self.request_windows.clear()
        self.blocked_endpoints.clear()
        self.endpoint_statistics.clear()

        logger.info("Rate Limit Anomaly Detector cleanup completed")
