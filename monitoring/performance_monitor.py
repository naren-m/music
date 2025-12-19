"""
Performance Monitoring and Analytics for Carnatic Music Learning Platform
Real-time performance metrics, user analytics, and system health monitoring
"""

import time
import json
import logging
from datetime import datetime, timedelta
from functools import wraps
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, asdict
from collections import defaultdict, deque
import threading
import psutil
import sys
import os

# Add project root to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


@dataclass
class PerformanceMetric:
    """Individual performance metric data structure"""
    timestamp: datetime
    metric_type: str
    value: float
    metadata: Dict[str, Any]
    user_id: Optional[str] = None
    session_id: Optional[str] = None


@dataclass
class SystemHealth:
    """System health snapshot"""
    timestamp: datetime
    cpu_usage: float
    memory_usage: float
    disk_usage: float
    active_connections: int
    response_time_avg: float
    error_rate: float


class PerformanceMonitor:
    """
    Real-time performance monitoring system for production deployment
    """

    def __init__(self, max_history_size: int = 10000):
        self.max_history_size = max_history_size
        self.metrics_history: deque = deque(maxlen=max_history_size)
        self.response_times: defaultdict = defaultdict(list)
        self.error_counts: defaultdict = defaultdict(int)
        self.user_sessions: Dict[str, Dict] = {}
        self.system_alerts: List[Dict] = []

        # Performance thresholds
        self.thresholds = {
            'response_time_warning': 500,  # ms
            'response_time_critical': 1000,  # ms
            'cpu_usage_warning': 70,  # %
            'cpu_usage_critical': 85,  # %
            'memory_usage_warning': 80,  # %
            'memory_usage_critical': 90,  # %
            'error_rate_warning': 1,  # %
            'error_rate_critical': 5,  # %
        }

        self.lock = threading.Lock()
        self._setup_logging()

    def _setup_logging(self):
        """Setup logging for performance monitoring"""
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler('logs/performance.log'),
                logging.StreamHandler()
            ]
        )
        self.logger = logging.getLogger('PerformanceMonitor')

    def record_response_time(self, endpoint: str, response_time: float,
                           status_code: int, user_id: Optional[str] = None):
        """Record API response time"""
        with self.lock:
            metric = PerformanceMetric(
                timestamp=datetime.now(),
                metric_type='response_time',
                value=response_time,
                metadata={
                    'endpoint': endpoint,
                    'status_code': status_code
                },
                user_id=user_id
            )

            self.metrics_history.append(metric)
            self.response_times[endpoint].append(response_time)

            # Keep only recent response times for rolling averages
            if len(self.response_times[endpoint]) > 100:
                self.response_times[endpoint] = self.response_times[endpoint][-100:]

            # Check for performance issues
            if response_time > self.thresholds['response_time_warning']:
                self._create_alert(
                    'response_time_slow',
                    f"Slow response on {endpoint}: {response_time}ms",
                    'warning' if response_time < self.thresholds['response_time_critical'] else 'critical'
                )

    def record_error(self, endpoint: str, error_type: str, error_message: str,
                    user_id: Optional[str] = None):
        """Record application error"""
        with self.lock:
            metric = PerformanceMetric(
                timestamp=datetime.now(),
                metric_type='error',
                value=1,
                metadata={
                    'endpoint': endpoint,
                    'error_type': error_type,
                    'error_message': error_message
                },
                user_id=user_id
            )

            self.metrics_history.append(metric)
            self.error_counts[endpoint] += 1

            self.logger.error(f"Error on {endpoint}: {error_type} - {error_message}")

    def record_user_activity(self, user_id: str, activity_type: str,
                           exercise_type: Optional[str] = None,
                           performance_score: Optional[float] = None):
        """Record user activity and performance"""
        with self.lock:
            if user_id not in self.user_sessions:
                self.user_sessions[user_id] = {
                    'start_time': datetime.now(),
                    'activities': [],
                    'total_practice_time': 0,
                    'exercises_completed': 0,
                    'average_score': 0
                }

            activity = {
                'timestamp': datetime.now(),
                'type': activity_type,
                'exercise_type': exercise_type,
                'performance_score': performance_score
            }

            self.user_sessions[user_id]['activities'].append(activity)

            if activity_type == 'exercise_completed':
                self.user_sessions[user_id]['exercises_completed'] += 1
                if performance_score:
                    # Update average score
                    current_avg = self.user_sessions[user_id]['average_score']
                    completed = self.user_sessions[user_id]['exercises_completed']
                    new_avg = ((current_avg * (completed - 1)) + performance_score) / completed
                    self.user_sessions[user_id]['average_score'] = new_avg

    def get_system_health(self) -> SystemHealth:
        """Get current system health metrics"""
        # CPU and Memory usage
        cpu_percent = psutil.cpu_percent(interval=1)
        memory = psutil.virtual_memory()
        disk = psutil.disk_usage('/')

        # Network connections (approximate active users)
        connections = len(psutil.net_connections(kind='inet'))

        # Calculate average response time (last 100 requests)
        recent_response_times = []
        for endpoint_times in self.response_times.values():
            recent_response_times.extend(endpoint_times[-10:])  # Last 10 per endpoint

        avg_response_time = sum(recent_response_times) / len(recent_response_times) if recent_response_times else 0

        # Calculate error rate (last hour)
        hour_ago = datetime.now() - timedelta(hours=1)
        recent_errors = sum(1 for metric in self.metrics_history
                          if metric.timestamp > hour_ago and metric.metric_type == 'error')
        recent_requests = sum(1 for metric in self.metrics_history
                            if metric.timestamp > hour_ago and metric.metric_type == 'response_time')

        error_rate = (recent_errors / recent_requests * 100) if recent_requests > 0 else 0

        health = SystemHealth(
            timestamp=datetime.now(),
            cpu_usage=cpu_percent,
            memory_usage=memory.percent,
            disk_usage=disk.percent,
            active_connections=connections,
            response_time_avg=avg_response_time,
            error_rate=error_rate
        )

        # Check for system health alerts
        self._check_system_health_alerts(health)

        return health

    def _check_system_health_alerts(self, health: SystemHealth):
        """Check system health against thresholds and create alerts"""
        if health.cpu_usage > self.thresholds['cpu_usage_warning']:
            severity = 'critical' if health.cpu_usage > self.thresholds['cpu_usage_critical'] else 'warning'
            self._create_alert('high_cpu_usage', f"CPU usage: {health.cpu_usage}%", severity)

        if health.memory_usage > self.thresholds['memory_usage_warning']:
            severity = 'critical' if health.memory_usage > self.thresholds['memory_usage_critical'] else 'warning'
            self._create_alert('high_memory_usage', f"Memory usage: {health.memory_usage}%", severity)

        if health.error_rate > self.thresholds['error_rate_warning']:
            severity = 'critical' if health.error_rate > self.thresholds['error_rate_critical'] else 'warning'
            self._create_alert('high_error_rate', f"Error rate: {health.error_rate}%", severity)

    def _create_alert(self, alert_type: str, message: str, severity: str):
        """Create system alert"""
        alert = {
            'timestamp': datetime.now(),
            'type': alert_type,
            'message': message,
            'severity': severity
        }

        self.system_alerts.append(alert)

        # Keep only recent alerts
        if len(self.system_alerts) > 1000:
            self.system_alerts = self.system_alerts[-1000:]

        # Log critical alerts
        if severity == 'critical':
            self.logger.critical(f"CRITICAL ALERT: {alert_type} - {message}")
        else:
            self.logger.warning(f"WARNING: {alert_type} - {message}")

    def get_performance_summary(self, hours: int = 24) -> Dict[str, Any]:
        """Get performance summary for specified time period"""
        cutoff_time = datetime.now() - timedelta(hours=hours)
        recent_metrics = [m for m in self.metrics_history if m.timestamp > cutoff_time]

        # Response time statistics
        response_times = [m.value for m in recent_metrics if m.metric_type == 'response_time']
        avg_response_time = sum(response_times) / len(response_times) if response_times else 0

        # Error statistics
        errors = [m for m in recent_metrics if m.metric_type == 'error']
        error_rate = len(errors) / len(recent_metrics) * 100 if recent_metrics else 0

        # Endpoint statistics
        endpoint_stats = defaultdict(lambda: {'count': 0, 'avg_response_time': 0, 'errors': 0})
        for metric in recent_metrics:
            endpoint = metric.metadata.get('endpoint', 'unknown')
            if metric.metric_type == 'response_time':
                endpoint_stats[endpoint]['count'] += 1
                endpoint_stats[endpoint]['avg_response_time'] += metric.value
            elif metric.metric_type == 'error':
                endpoint_stats[endpoint]['errors'] += 1

        # Calculate averages
        for stats in endpoint_stats.values():
            if stats['count'] > 0:
                stats['avg_response_time'] /= stats['count']

        # User activity statistics
        active_users = len([s for s in self.user_sessions.values()
                          if (datetime.now() - s['start_time']).seconds < 3600])  # Active in last hour

        total_exercises = sum(s['exercises_completed'] for s in self.user_sessions.values())
        avg_user_score = sum(s['average_score'] for s in self.user_sessions.values()) / len(self.user_sessions) if self.user_sessions else 0

        return {
            'summary_period_hours': hours,
            'total_requests': len(response_times),
            'average_response_time_ms': round(avg_response_time, 2),
            'error_rate_percent': round(error_rate, 2),
            'active_users_last_hour': active_users,
            'total_exercises_completed': total_exercises,
            'average_user_score': round(avg_user_score, 2),
            'endpoint_statistics': dict(endpoint_stats),
            'recent_alerts': [alert for alert in self.system_alerts if alert['timestamp'] > cutoff_time]
        }

    def get_real_time_metrics(self) -> Dict[str, Any]:
        """Get real-time metrics for dashboard"""
        system_health = self.get_system_health()

        # Recent response times (last 10 requests)
        recent_response_times = []
        for metric in reversed(list(self.metrics_history)[-50:]):
            if metric.metric_type == 'response_time':
                recent_response_times.append(metric.value)
            if len(recent_response_times) >= 10:
                break

        return {
            'system_health': asdict(system_health),
            'recent_response_times': recent_response_times,
            'active_users': len([s for s in self.user_sessions.values()
                               if (datetime.now() - s['start_time']).seconds < 300]),  # Active in last 5 min
            'recent_alerts': self.system_alerts[-5:] if self.system_alerts else []
        }

    def export_metrics(self, format: str = 'json', hours: int = 24) -> str:
        """Export metrics data for external analysis"""
        cutoff_time = datetime.now() - timedelta(hours=hours)
        recent_metrics = [m for m in self.metrics_history if m.timestamp > cutoff_time]

        if format == 'json':
            # Convert metrics to serializable format
            serializable_metrics = []
            for metric in recent_metrics:
                metric_dict = asdict(metric)
                metric_dict['timestamp'] = metric.timestamp.isoformat()
                serializable_metrics.append(metric_dict)

            return json.dumps({
                'export_timestamp': datetime.now().isoformat(),
                'period_hours': hours,
                'metrics': serializable_metrics,
                'summary': self.get_performance_summary(hours)
            }, indent=2)

        return "Unsupported format"

    def cleanup_old_data(self, days: int = 7):
        """Cleanup old monitoring data"""
        cutoff_time = datetime.now() - timedelta(days=days)

        with self.lock:
            # Clean up metrics history
            original_size = len(self.metrics_history)
            self.metrics_history = deque(
                [m for m in self.metrics_history if m.timestamp > cutoff_time],
                maxlen=self.max_history_size
            )

            # Clean up user sessions
            active_sessions = {}
            for user_id, session in self.user_sessions.items():
                if session['start_time'] > cutoff_time:
                    active_sessions[user_id] = session
            self.user_sessions = active_sessions

            # Clean up alerts
            self.system_alerts = [alert for alert in self.system_alerts if alert['timestamp'] > cutoff_time]

            cleaned_count = original_size - len(self.metrics_history)
            if cleaned_count > 0:
                self.logger.info(f"Cleaned up {cleaned_count} old metrics records")


# Global performance monitor instance
performance_monitor = PerformanceMonitor()


def monitor_request(endpoint: str):
    """Decorator to monitor request performance"""
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            start_time = time.time()
            try:
                result = func(*args, **kwargs)
                response_time = (time.time() - start_time) * 1000  # Convert to milliseconds

                # Determine status code from result
                status_code = 200
                if hasattr(result, 'status_code'):
                    status_code = result.status_code

                performance_monitor.record_response_time(endpoint, response_time, status_code)
                return result

            except Exception as e:
                response_time = (time.time() - start_time) * 1000
                performance_monitor.record_response_time(endpoint, response_time, 500)
                performance_monitor.record_error(endpoint, type(e).__name__, str(e))
                raise
        return wrapper
    return decorator


if __name__ == '__main__':
    # Example usage and testing
    monitor = PerformanceMonitor()

    # Simulate some metrics
    monitor.record_response_time('/api/health', 45.2, 200)
    monitor.record_response_time('/api/exercises/sarali', 123.4, 200)
    monitor.record_error('/api/exercises/invalid', 'ValueError', 'Invalid exercise type')

    # Get performance summary
    summary = monitor.get_performance_summary()
    print("Performance Summary:")
    print(json.dumps(summary, indent=2, default=str))

    # Get system health
    health = monitor.get_system_health()
    print(f"\nSystem Health: CPU {health.cpu_usage}%, Memory {health.memory_usage}%")