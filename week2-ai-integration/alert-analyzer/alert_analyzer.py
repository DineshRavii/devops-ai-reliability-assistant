#!/usr/bin/env python3
"""
AI-Powered Alert Analyzer V2
- Slack notifications
- Alert correlation
- Anomaly detection (FIXED)
"""

from openai import OpenAI
import requests
import json
import time
import os
from datetime import datetime, timedelta
from typing import List, Dict, Optional
from collections import defaultdict

class AlertAnalyzer:
    def __init__(self, 
                 openai_api_key: str,
                 slack_webhook_url: Optional[str] = None,
                 prometheus_url: str = "http://prometheus:9090",
                 model: str = "gpt-4o-mini"):
        """Enhanced Alert Analyzer with Slack and anomaly detection"""
        self.client = OpenAI(api_key=openai_api_key)
        self.prometheus_url = prometheus_url
        self.model = model
        self.slack_webhook = slack_webhook_url
        
        # Tracking
        self.analyzed_alerts = set()
        self.alert_history = []
        self.metric_baselines = {}
        self.total_cost = 0.0
        
        print(f"🤖 AI Model: {model}")
        if slack_webhook_url:
            print(f"💬 Slack: Enabled")
        else:
            print(f"💬 Slack: Disabled (no webhook)")
        print(f"📊 Prometheus: {prometheus_url}")
        print()
        
    def get_active_alerts(self) -> List[Dict]:
        """Fetch firing alerts from Prometheus"""
        try:
            response = requests.get(
                f"{self.prometheus_url}/api/v1/alerts",
                timeout=5
            )
            response.raise_for_status()
            data = response.json()
            
            if data['status'] != 'success':
                return []
            
            firing_alerts = [a for a in data['data']['alerts'] if a['state'] == 'firing']
            return firing_alerts
            
        except Exception as e:
            print(f"❌ Error fetching alerts: {e}")
            return []
    
    def get_metric_value(self, query: str) -> Optional[float]:
        """Query Prometheus for a metric value"""
        try:
            response = requests.get(
                f"{self.prometheus_url}/api/v1/query",
                params={'query': query},
                timeout=5
            )
            
            if response.status_code == 200:
                data = response.json()
                if data['status'] == 'success' and data['data']['result']:
                    return float(data['data']['result'][0]['value'][1])
            
            return None
        except Exception as e:
            print(f"❌ Metric query failed: {e}")
            return None
    
    def detect_anomalies(self) -> List[Dict]:
        """Detect anomalous metrics (baseline comparison) - FIXED"""
        anomalies = []
        
        metrics_to_check = {
            'request_rate': 'sum(rate(app_requests_total[5m]))',
            'error_rate': 'sum(rate(app_requests_total{status="500"}[5m]))',
            'p95_latency': 'histogram_quantile(0.95, rate(app_request_duration_seconds_bucket[5m]))'
        }
        
        for metric_name, query in metrics_to_check.items():
            current_value = self.get_metric_value(query)
            
            if current_value is None:
                continue
            
            # Ensure it's a float
            try:
                current_value = float(current_value)
            except (TypeError, ValueError):
                continue
            
            # Initialize baseline if first time
            if metric_name not in self.metric_baselines:
                self.metric_baselines[metric_name] = {
                    'values': [current_value],
                    'mean': current_value,
                    'std': 0.0
                }
                continue
            
            baseline = self.metric_baselines[metric_name]
            
            # Calculate if anomalous (>3 standard deviations)
            if baseline['std'] > 0:
                try:
                    z_score = abs((current_value - baseline['mean']) / baseline['std'])
                    
                    if z_score > 3:  # Statistical anomaly
                        anomalies.append({
                            'metric': metric_name,
                            'current': current_value,
                            'baseline': baseline['mean'],
                            'std': baseline['std'],
                            'z_score': z_score,
                            'severity': 'critical' if z_score > 5 else 'warning'
                        })
                except Exception as e:
                    print(f"⚠️  Z-score calculation error: {e}")
            
            # Update baseline (moving average)
            baseline['values'].append(current_value)
            if len(baseline['values']) > 100:  # Keep last 100 samples
                baseline['values'].pop(0)
            
            # Calculate statistics manually (FIXED - no more statistics.stdev)
            try:
                values = baseline['values']
                n = len(values)
                
                # Calculate mean
                baseline['mean'] = sum(values) / n
                
                # Calculate standard deviation manually
                if n > 1:
                    variance = sum((x - baseline['mean']) ** 2 for x in values) / (n - 1)
                    baseline['std'] = variance ** 0.5
                else:
                    baseline['std'] = 0.0
                    
            except Exception as e:
                print(f"⚠️  Baseline calculation warning for {metric_name}: {e}")
                baseline['std'] = 0.0
        
        return anomalies
    
    def correlate_alerts(self, alerts: List[Dict]) -> Dict:
        """Detect patterns across multiple alerts"""
        if len(alerts) < 2:
            return {'correlated': False}
        
        # Group by time window
        alert_names = [a['labels'].get('alertname') for a in alerts]
        
        # Check for known patterns
        patterns = {
            'cascade': ['HighErrorRate', 'HighLatency'],
            'outage': ['MetricsAppDown', 'LowRequestRate'],
        }
        
        for pattern_name, pattern_alerts in patterns.items():
            if all(alert in alert_names for alert in pattern_alerts):
                return {
                    'correlated': True,
                    'pattern': pattern_name,
                    'alerts': pattern_alerts,
                    'description': f"Detected {pattern_name} incident pattern"
                }
        
        return {'correlated': False}
    
    def analyze_alert_with_ai(self, alert: Dict, anomalies: List[Dict] = None, 
                            correlation: Dict = None) -> tuple[str, float]:
        """Enhanced AI analysis with anomaly and correlation context"""
        alert_name = alert['labels'].get('alertname', 'Unknown')
        severity = alert['labels'].get('severity', 'unknown')
        description = alert['annotations'].get('description', 'No description')
        
        # Build enhanced context
        context_parts = [
            f"Alert: {alert_name}",
            f"Severity: {severity}",
            f"Description: {description}"
        ]
        
        if anomalies:
            context_parts.append("\n**Detected Anomalies:**")
            for anomaly in anomalies:
                context_parts.append(
                    f"- {anomaly['metric']}: {anomaly['current']:.2f} "
                    f"(baseline: {anomaly['baseline']:.2f} ±{anomaly['std']:.2f}, "
                    f"z-score: {anomaly['z_score']:.1f})"
                )
        
        if correlation and correlation.get('correlated'):
            context_parts.append(f"\n**Pattern Detected:** {correlation['description']}")
            context_parts.append(f"Related alerts: {', '.join(correlation['alerts'])}")
        
        context = "\n".join(context_parts)
        
        prompt = f"""You are an expert DevOps/SRE engineer with AI-powered anomaly detection.

{context}

**Analysis Required:**

1. **Root Cause** (2-3 sentences considering anomalies/patterns)
2. **Impact Assessment** (1-2 sentences)
3. **Immediate Actions** (3 specific steps with kubectl commands)
4. **Prevention** (1-2 sentences)

Keep it actionable and concise."""

        try:
            print(f"🤖 Analyzing '{alert_name}' with AI...")
            
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "You are an expert DevOps/SRE engineer."},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=1000,
                temperature=0.7
            )
            
            analysis = response.choices[0].message.content
            
            # Calculate cost
            input_tokens = response.usage.prompt_tokens
            output_tokens = response.usage.completion_tokens
            cost = (input_tokens * 0.00000015) + (output_tokens * 0.0000006)
            self.total_cost += cost
            
            print(f"✅ Analysis complete! Cost: ${cost:.6f}")
            return analysis, cost
            
        except Exception as e:
            return f"❌ AI analysis failed: {e}", 0.0
    
    def send_to_slack(self, alert: Dict, analysis: str, 
                     anomalies: List[Dict] = None, correlation: Dict = None):
        """Send formatted alert to Slack"""
        if not self.slack_webhook:
            return
        
        alert_name = alert['labels'].get('alertname')
        severity = alert['labels'].get('severity', 'unknown')
        
        # Build Slack message
        blocks = [
            {
                "type": "header",
                "text": {
                    "type": "plain_text",
                    "text": f"🚨 Alert: {alert_name}"
                }
            },
            {
                "type": "section",
                "fields": [
                    {"type": "mrkdwn", "text": f"*Severity:*\n{severity.upper()}"},
                    {"type": "mrkdwn", "text": f"*Time:*\n{datetime.now().strftime('%H:%M:%S')}"}
                ]
            },
            {"type": "divider"}
        ]
        
        # Add anomaly info
        if anomalies:
            anomaly_text = "\n".join([
                f"• *{a['metric']}*: {a['current']:.2f} (baseline: {a['baseline']:.2f}, z-score: {a['z_score']:.1f})"
                for a in anomalies
            ])
            blocks.append({
                "type": "section",
                "text": {"type": "mrkdwn", "text": f"*🔍 Anomalies Detected:*\n{anomaly_text}"}
            })
        
        # Add correlation info
        if correlation and correlation.get('correlated'):
            blocks.append({
                "type": "section",
                "text": {"type": "mrkdwn", "text": f"*🔗 Pattern:* {correlation['description']}"}
            })
        
        blocks.append({"type": "divider"})
        
        # Add AI analysis (truncate to Slack limit)
        analysis_truncated = analysis[:2800] if len(analysis) > 2800 else analysis
        blocks.append({
            "type": "section",
            "text": {"type": "mrkdwn", "text": f"*🤖 AI Analysis:*\n{analysis_truncated}"}
        })
        
        try:
            response = requests.post(
                self.slack_webhook,
                json={"blocks": blocks},
                timeout=5
            )
            
            if response.status_code == 200:
                print(f"💬 Sent to Slack!")
            else:
                print(f"❌ Slack error: {response.status_code}")
                
        except Exception as e:
            print(f"❌ Slack send failed: {e}")
    
    def format_alert_report(self, alert: Dict, analysis: str, cost: float, 
                          anomalies: List[Dict] = None, correlation: Dict = None) -> str:
        """Enhanced report with anomalies and correlation"""
        alert_name = alert['labels'].get('alertname', 'Unknown')
        severity = alert['labels'].get('severity', 'unknown')
        
        report = f"""
{'='*80}
🚨 ALERT ANALYSIS REPORT
{'='*80}

Alert: {alert_name}
Severity: {severity}
Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
Analysis Cost: ${cost:.6f}
"""
        
        if anomalies:
            report += f"\n{'-'*80}\n🔍 ANOMALIES DETECTED\n{'-'*80}\n\n"
            for anomaly in anomalies:
                report += f"{anomaly['metric'].upper()}:\n"
                report += f"  Current: {anomaly['current']:.4f}\n"
                report += f"  Baseline: {anomaly['baseline']:.4f} (±{anomaly['std']:.4f})\n"
                report += f"  Z-Score: {anomaly['z_score']:.2f} ({anomaly['severity']})\n\n"
        
        if correlation and correlation.get('correlated'):
            report += f"\n{'-'*80}\n🔗 CORRELATION DETECTED\n{'-'*80}\n\n"
            report += f"Pattern: {correlation['pattern']}\n"
            report += f"Description: {correlation['description']}\n"
            report += f"Related Alerts: {', '.join(correlation['alerts'])}\n\n"
        
        report += f"\n{'-'*80}\n🤖 AI ANALYSIS\n{'-'*80}\n\n{analysis}\n\n{'='*80}\n"
        
        return report
    
    def monitor_and_analyze(self, interval: int = 30):
        """Main monitoring loop with all features"""
        print("🚀 Enhanced Alert Analyzer Started!")
        print(f"{'='*80}\n")
        
        iteration = 0
        
        while True:
            try:
                iteration += 1
                timestamp = datetime.now().strftime('%H:%M:%S')
                
                # Check for anomalies
                anomalies = self.detect_anomalies()
                if anomalies:
                    print(f"🔍 [{timestamp}] Detected {len(anomalies)} anomalies")
                
                # Get current alerts
                alerts = self.get_active_alerts()
                
                if not alerts:
                    print(f"✅ [{timestamp}] Iteration {iteration}: No firing alerts")
                else:
                    print(f"🔥 [{timestamp}] Iteration {iteration}: {len(alerts)} alert(s)")
                    
                    # Check correlation
                    correlation = self.correlate_alerts(alerts)
                    if correlation.get('correlated'):
                        print(f"🔗 Correlation: {correlation['description']}")
                    
                    # Analyze each new alert
                    for alert in alerts:
                        alert_id = f"{alert['labels'].get('alertname')}_{alert.get('activeAt')}"
                        
                        if alert_id in self.analyzed_alerts:
                            continue
                        
                        print(f"\n🆕 NEW: {alert['labels'].get('alertname')}")
                        
                        # AI analysis with context
                        analysis, cost = self.analyze_alert_with_ai(alert, anomalies, correlation)
                        
                        # Generate report
                        report = self.format_alert_report(alert, analysis, cost, anomalies, correlation)
                        print(report)
                        
                        # Send to Slack
                        self.send_to_slack(alert, analysis, anomalies, correlation)
                        
                        # Save report
                        safe_id = alert_id.replace(':', '_').replace('/', '_')
                        filename = f"alert_analysis_{safe_id}.txt"
                        try:
                            with open(filename, 'w') as f:
                                f.write(report)
                            print(f"💾 Saved: {filename}\n")
                        except Exception as e:
                            print(f"❌ Save failed: {e}\n")
                        
                        self.analyzed_alerts.add(alert_id)
                        self.alert_history.append({
                            'alert': alert,
                            'timestamp': datetime.now(),
                            'analysis': analysis
                        })
                
                time.sleep(interval)
                
            except KeyboardInterrupt:
                print(f"\n\n{'='*80}")
                print("👋 Shutting down...")
                print(f"💰 Total cost: ${self.total_cost:.6f}")
                print(f"📊 Alerts analyzed: {len(self.analyzed_alerts)}")
                print(f"🔍 Baseline metrics tracked: {len(self.metric_baselines)}")
                print(f"{'='*80}\n")
                break
            except Exception as e:
                print(f"❌ Error: {e}")
                time.sleep(interval)


def main():
    """Main entry point"""
    openai_key = os.getenv('OPENAI_API_KEY')
    if not openai_key:
        print("❌ OPENAI_API_KEY not set!")
        return
    
    slack_webhook = os.getenv('SLACK_WEBHOOK_URL')
    if not slack_webhook:
        print("⚠️  SLACK_WEBHOOK_URL not set - Slack disabled")
    
    prometheus_url = os.getenv('PROMETHEUS_URL', 'http://prometheus:9090')
    
    analyzer = AlertAnalyzer(
        openai_api_key=openai_key,
        slack_webhook_url=slack_webhook,
        prometheus_url=prometheus_url,
        model="gpt-4o-mini"
    )
    
    analyzer.monitor_and_analyze(interval=30)


if __name__ == '__main__':
    main()