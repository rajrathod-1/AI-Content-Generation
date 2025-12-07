"""
Metrics collection and monitoring for the AI Content Generation Service
"""
import time
import threading
from collections import defaultdict, deque
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, asdict
import json
import psutil
import logging
from datetime import datetime, timedelta

@dataclass
class RequestMetrics:
    """Metrics for individual requests"""
    endpoint: str
    method: str
    status_code: int
    response_time: float
    timestamp: float
    user_id: Optional[str] = None
    tokens_used: int = 0
    cache_hit: bool = False

@dataclass
class SystemMetrics:
    """System resource metrics"""
    cpu_percent: float
    memory_percent: float
    memory_used_mb: float
    disk_usage_percent: float
    active_connections: int
    timestamp: float

@dataclass
class ServiceMetrics:
    """Service-specific metrics"""
    service_name: str
    total_requests: int
    successful_requests: int
    failed_requests: int
    average_response_time: float
    cache_hit_rate: float
    tokens_consumed: int
    uptime_seconds: float

class MetricsCollector:
    """Comprehensive metrics collection system"""
    
    def __init__(self, max_history: int = 1000):
        self.max_history = max_history
        self.start_time = time.time()
        self.logger = logging.getLogger(__name__)
        
        # Request metrics storage
        self.request_history = deque(maxlen=max_history)
        self.system_history = deque(maxlen=max_history)
        
        # Real-time counters
        self.counters = defaultdict(int)
        self.timers = defaultdict(float)
        self.gauges = defaultdict(float)
        
        # Service metrics
        self.service_stats = defaultdict(lambda: {
            'total_requests': 0,
            'successful_requests': 0,
            'failed_requests': 0,
            'total_response_time': 0.0,
            'cache_hits': 0,
            'tokens_used': 0
        })
        
        # Thread safety
        self.lock = threading.RLock()
        
        # Performance tracking
        self.response_time_buckets = {
            '0-50ms': 0,
            '50-100ms': 0,
            '100-200ms': 0,
            '200-500ms': 0,
            '500ms+': 0
        }
        
        # Error tracking
        self.error_counts = defaultdict(int)
        self.error_history = deque(maxlen=100)
        
        # User activity tracking
        self.active_users = set()
        self.user_request_counts = defaultdict(int)
        
        # Start system monitoring
        self._start_system_monitoring()
    
    def start_timer(self) -> float:
        """Start a timer and return the start time"""
        return time.time()
    
    def end_timer(self, start_time: float) -> float:
        """End a timer and return elapsed time in milliseconds"""
        return (time.time() - start_time) * 1000
    
    def record_request(
        self,
        endpoint: str,
        response_time_ms: float,
        success: bool,
        method: str = 'POST',
        user_id: Optional[str] = None,
        tokens_used: int = 0,
        cache_hit: bool = False
    ):
        """Record a request metric"""
        with self.lock:
            # Create request metric
            metric = RequestMetrics(
                endpoint=endpoint,
                method=method,
                status_code=200 if success else 500,
                response_time=response_time_ms,
                timestamp=time.time(),
                user_id=user_id,
                tokens_used=tokens_used,
                cache_hit=cache_hit
            )
            
            # Store in history
            self.request_history.append(metric)
            
            # Update counters
            self.counters['total_requests'] += 1
            if success:
                self.counters['successful_requests'] += 1
            else:
                self.counters['failed_requests'] += 1
                self.error_counts[endpoint] += 1
                self.error_history.append({
                    'endpoint': endpoint,
                    'timestamp': time.time(),
                    'error_type': 'request_failure'
                })
            
            # Update response time buckets
            self._update_response_time_bucket(response_time_ms)
            
            # Update service stats
            service_key = endpoint.split('/')[1] if '/' in endpoint else 'unknown'
            stats = self.service_stats[service_key]
            stats['total_requests'] += 1
            if success:
                stats['successful_requests'] += 1
            else:
                stats['failed_requests'] += 1
            stats['total_response_time'] += response_time_ms
            stats['tokens_used'] += tokens_used
            if cache_hit:
                stats['cache_hits'] += 1
            
            # Track user activity
            if user_id:
                self.active_users.add(user_id)
                self.user_request_counts[user_id] += 1
    
    def _update_response_time_bucket(self, response_time_ms: float):
        """Update response time distribution buckets"""
        if response_time_ms < 50:
            self.response_time_buckets['0-50ms'] += 1
        elif response_time_ms < 100:
            self.response_time_buckets['50-100ms'] += 1
        elif response_time_ms < 200:
            self.response_time_buckets['100-200ms'] += 1
        elif response_time_ms < 500:
            self.response_time_buckets['200-500ms'] += 1
        else:
            self.response_time_buckets['500ms+'] += 1
    
    def record_error(self, endpoint: str, error_type: str, error_message: str):
        """Record an error"""
        with self.lock:
            self.error_counts[f"{endpoint}:{error_type}"] += 1
            self.error_history.append({
                'endpoint': endpoint,
                'error_type': error_type,
                'error_message': error_message,
                'timestamp': time.time()
            })
    
    def set_gauge(self, name: str, value: float):
        """Set a gauge metric"""
        with self.lock:
            self.gauges[name] = value
    
    def increment_counter(self, name: str, value: int = 1):
        """Increment a counter"""
        with self.lock:
            self.counters[name] += value
    
    def get_current_timestamp(self) -> float:
        """Get current timestamp"""
        return time.time()
    
    def get_uptime(self) -> float:
        """Get service uptime in seconds"""
        return time.time() - self.start_time
    
    def get_metrics(self) -> Dict[str, Any]:
        """Get comprehensive metrics summary"""
        with self.lock:
            current_time = time.time()
            uptime = current_time - self.start_time
            
            # Calculate averages
            total_requests = self.counters['total_requests']
            avg_response_time = 0.0
            if total_requests > 0:
                total_response_time = sum(req.response_time for req in self.request_history)
                avg_response_time = total_response_time / len(self.request_history)
            
            # Calculate success rate
            success_rate = 0.0
            if total_requests > 0:
                success_rate = self.counters['successful_requests'] / total_requests
            
            # Calculate cache hit rate
            cache_hits = sum(1 for req in self.request_history if req.cache_hit)
            cache_hit_rate = cache_hits / len(self.request_history) if self.request_history else 0.0
            
            # Get recent metrics (last 5 minutes)
            recent_cutoff = current_time - 300  # 5 minutes
            recent_requests = [req for req in self.request_history if req.timestamp > recent_cutoff]
            
            recent_avg_response_time = 0.0
            if recent_requests:
                recent_avg_response_time = sum(req.response_time for req in recent_requests) / len(recent_requests)
            
            # System metrics
            system_metrics = self._get_current_system_metrics()
            
            return {
                'timestamp': current_time,
                'uptime_seconds': uptime,
                'uptime_human': self._format_uptime(uptime),
                'total_requests': total_requests,
                'successful_requests': self.counters['successful_requests'],
                'failed_requests': self.counters['failed_requests'],
                'success_rate': success_rate,
                'average_response_time_ms': avg_response_time,
                'recent_average_response_time_ms': recent_avg_response_time,
                'cache_hit_rate': cache_hit_rate,
                'total_tokens_used': sum(req.tokens_used for req in self.request_history),
                'active_users_count': len(self.active_users),
                'requests_per_minute': len(recent_requests) * (60 / 300),  # Scale to per minute
                'response_time_distribution': self.response_time_buckets.copy(),
                'error_summary': dict(self.error_counts),
                'service_breakdown': self._get_service_metrics(),
                'system_metrics': asdict(system_metrics) if system_metrics else {},
                'top_users': self._get_top_users(),
                'health_score': self._calculate_health_score()
            }
    
    def _get_service_metrics(self) -> Dict[str, Dict]:
        """Get per-service metrics breakdown"""
        service_metrics = {}
        
        for service_name, stats in self.service_stats.items():
            total_requests = stats['total_requests']
            if total_requests > 0:
                service_metrics[service_name] = {
                    'total_requests': total_requests,
                    'success_rate': stats['successful_requests'] / total_requests,
                    'average_response_time_ms': stats['total_response_time'] / total_requests,
                    'cache_hit_rate': stats['cache_hits'] / total_requests,
                    'tokens_used': stats['tokens_used']
                }
        
        return service_metrics
    
    def _get_top_users(self, limit: int = 10) -> List[Dict]:
        """Get top users by request count"""
        sorted_users = sorted(
            self.user_request_counts.items(),
            key=lambda x: x[1],
            reverse=True
        )[:limit]
        
        return [{'user_id': user_id, 'request_count': count} for user_id, count in sorted_users]
    
    def _calculate_health_score(self) -> float:
        """Calculate overall system health score (0-100)"""
        score = 100.0
        
        # Deduct points for errors
        total_requests = self.counters['total_requests']
        if total_requests > 0:
            error_rate = self.counters['failed_requests'] / total_requests
            score -= error_rate * 50  # Up to 50 points for errors
        
        # Deduct points for slow responses
        if hasattr(self, 'request_history') and self.request_history:
            avg_response_time = sum(req.response_time for req in self.request_history) / len(self.request_history)
            if avg_response_time > 200:  # Over 200ms
                score -= min(25, (avg_response_time - 200) / 10)  # Up to 25 points for slowness
        
        # Deduct points for high resource usage
        try:
            cpu_percent = psutil.cpu_percent()
            memory_percent = psutil.virtual_memory().percent
            
            if cpu_percent > 80:
                score -= (cpu_percent - 80) / 2  # Up to 10 points
            if memory_percent > 80:
                score -= (memory_percent - 80) / 2  # Up to 10 points
        except:
            pass
        
        return max(0, min(100, score))
    
    def _format_uptime(self, seconds: float) -> str:
        """Format uptime in human readable form"""
        uptime_delta = timedelta(seconds=int(seconds))
        return str(uptime_delta)
    
    def _get_current_system_metrics(self) -> Optional[SystemMetrics]:
        """Get current system resource metrics"""
        try:
            cpu_percent = psutil.cpu_percent(interval=1)
            memory = psutil.virtual_memory()
            disk = psutil.disk_usage('/')
            
            # Count network connections (approximate active connections)
            connections = len(psutil.net_connections(kind='inet'))
            
            return SystemMetrics(
                cpu_percent=cpu_percent,
                memory_percent=memory.percent,
                memory_used_mb=memory.used / (1024 * 1024),
                disk_usage_percent=disk.percent,
                active_connections=connections,
                timestamp=time.time()
            )
        except Exception as e:
            self.logger.error(f"Error collecting system metrics: {str(e)}")
            return None
    
    def _start_system_monitoring(self):
        """Start periodic system metrics collection"""
        def collect_system_metrics():
            while True:
                try:
                    metrics = self._get_current_system_metrics()
                    if metrics:
                        with self.lock:
                            self.system_history.append(metrics)
                except Exception as e:
                    self.logger.error(f"System monitoring error: {str(e)}")
                
                time.sleep(60)  # Collect every minute
        
        # Start monitoring in background thread
        monitor_thread = threading.Thread(target=collect_system_metrics, daemon=True)
        monitor_thread.start()
    
    def get_recent_errors(self, limit: int = 10) -> List[Dict]:
        """Get recent errors"""
        with self.lock:
            return list(self.error_history)[-limit:]
    
    def get_performance_summary(self, time_window_minutes: int = 60) -> Dict:
        """Get performance summary for a time window"""
        with self.lock:
            cutoff_time = time.time() - (time_window_minutes * 60)
            recent_requests = [req for req in self.request_history if req.timestamp > cutoff_time]
            
            if not recent_requests:
                return {'message': 'No requests in the specified time window'}
            
            response_times = [req.response_time for req in recent_requests]
            successful_requests = [req for req in recent_requests if req.status_code < 400]
            
            return {
                'time_window_minutes': time_window_minutes,
                'total_requests': len(recent_requests),
                'successful_requests': len(successful_requests),
                'success_rate': len(successful_requests) / len(recent_requests),
                'average_response_time_ms': sum(response_times) / len(response_times),
                'min_response_time_ms': min(response_times),
                'max_response_time_ms': max(response_times),
                'median_response_time_ms': sorted(response_times)[len(response_times) // 2],
                'p95_response_time_ms': sorted(response_times)[int(len(response_times) * 0.95)],
                'total_tokens_used': sum(req.tokens_used for req in recent_requests),
                'cache_hit_rate': sum(1 for req in recent_requests if req.cache_hit) / len(recent_requests)
            }
    
    def export_metrics(self, format_type: str = 'json') -> str:
        """Export metrics in various formats"""
        metrics = self.get_metrics()
        
        if format_type.lower() == 'json':
            return json.dumps(metrics, indent=2, default=str)
        elif format_type.lower() == 'prometheus':
            # Basic Prometheus format export
            lines = []
            lines.append(f"# HELP total_requests Total number of requests")
            lines.append(f"# TYPE total_requests counter")
            lines.append(f"total_requests {metrics['total_requests']}")
            
            lines.append(f"# HELP success_rate Request success rate")
            lines.append(f"# TYPE success_rate gauge")
            lines.append(f"success_rate {metrics['success_rate']}")
            
            lines.append(f"# HELP average_response_time_ms Average response time in milliseconds")
            lines.append(f"# TYPE average_response_time_ms gauge")
            lines.append(f"average_response_time_ms {metrics['average_response_time_ms']}")
            
            return '\n'.join(lines)
        else:
            return str(metrics)
    
    def reset_metrics(self):
        """Reset all metrics (useful for testing)"""
        with self.lock:
            self.request_history.clear()
            self.system_history.clear()
            self.counters.clear()
            self.timers.clear()
            self.gauges.clear()
            self.service_stats.clear()
            self.response_time_buckets = {key: 0 for key in self.response_time_buckets}
            self.error_counts.clear()
            self.error_history.clear()
            self.active_users.clear()
            self.user_request_counts.clear()
            self.start_time = time.time()

# Example usage
if __name__ == "__main__":
    import random
    
    # Initialize metrics collector
    metrics = MetricsCollector()
    
    # Simulate some requests
    for i in range(100):
        endpoint = random.choice(['/api/generate', '/api/search', '/api/ingest'])
        response_time = random.uniform(50, 300)
        success = random.random() > 0.1  # 90% success rate
        user_id = f"user_{random.randint(1, 20)}"
        tokens = random.randint(10, 500)
        cache_hit = random.random() > 0.7  # 30% cache hit rate
        
        metrics.record_request(
            endpoint=endpoint,
            response_time_ms=response_time,
            success=success,
            user_id=user_id,
            tokens_used=tokens,
            cache_hit=cache_hit
        )
        
        time.sleep(0.01)  # Small delay
    
    # Get metrics summary
    summary = metrics.get_metrics()
    print(json.dumps(summary, indent=2, default=str))
    
    # Get performance summary
    perf_summary = metrics.get_performance_summary(60)
    print(f"\nPerformance Summary: {perf_summary}")
    
    # Export in Prometheus format
    prometheus_export = metrics.export_metrics('prometheus')
    print(f"\nPrometheus Export:\n{prometheus_export}")