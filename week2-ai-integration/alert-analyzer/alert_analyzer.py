#!/usr/bin/env python3
"""
AI-Powered Alert Analyzer V2
- Slack notifications
- Alert correlation  
- Anomaly detection
- FIXED: Better deduplication (no duplicate Slack messages!)
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
                    pass
            
            # Update baseline (moving average)
            baseline['values'].append(current_value)
            if len(baseline['values']) > 100:
                baseline['values'].pop(0)
            
            # Calculate statistics manually (FIXED)
            try:
                values = baseline['values']
                n = len(values)
                baseline['mean'] = sum(values) / n
                
                if n > 1:
                    variance = sum((x - baseline['mean']) ** 2 for x in values) / (n - 1)
                    baseline['std'] = variance ** 0.5
                else:
                    baseline['std'] = 0.0
            except Exception:
                baseline['std'] = 0.0
        
        return anomalies
    
    def correlate_alerts(self, alerts: List[Dict]) -> Dict:
        """Detect patterns across multiple alerts"""
        if len(alerts) < 2:
            return {'correlated': False}
        
        alert_names = [a['labels'].get('alertname') for a in alerts]
        
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
        """Enhanced AI analysis"""
        alert_name = alert['labels'].get('alertname', 'Unknown')
        severity = alert['labels'].get('severity', 'unknown')
        description = alert['annotations'].get('description', 'No description')
        
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
            context_parts.append(f"\n**Pattern:** {correlation['description']}")
        
        context = "\n".join(context_parts)
        
        prompt = f"""You are an expert DevOps/SRE engineer.

{context}

Provide:
1. **Root Cause** (2-3 sentences)
2. **Impact** (1-2 sentences)
3. **Actions** (3 specific steps with kubectl commands)
4. **Prevention** (1-2 sentences)

Be concise and actionable."""

        try:
            print(f"🤖 Analyzing '{alert_name}'...")
            
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "You are an expert DevOps/SRE."},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=1000,
                temperature=0.7
            )
            
            analysis = response.choices[0].message.content
            input_tokens = response.usage.prompt_tokens
            output_tokens = response.usage.completion_tokens
            cost = (input_tokens * 0.00000015) + (output_tokens * 0.0000006)
            self.total_cost += cost
            
            print(f"✅ Complete! Cost: ${cost:.6f}")
            return analysis, cost
            
        except Exception as e:
            return f"❌ AI failed: {e}", 0.0
    
    def send_to_slack(self, alert: Dict, analysis: str, 
                     anomalies: List[Dict] = None, correlation: Dict = None):
        """Send to Slack"""
        if not self.slack_webhook:
            return
        
        alert_name = alert['labels'].get('alertname')
        severity = alert['labels'].get('severity', 'unknown')
        
        blocks = [
            {
                "type": "header",
                "text": {"type": "plain_text", "text": f"🚨 {alert_name}"}
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
        
        if anomalies:
            anomaly_text = "\n".join([
                f"• *{a['metric']}*: {a['current']:.2f} (z-score: {a['z_score']:.1f})"
                for a in anomalies
            ])
            blocks.append({
                "type": "section",
                "text": {"type": "mrkdwn", "text": f"*🔍 Anomalies:*\n{anomaly_text}"}
            })
        
        if correlation and correlation.get('correlated'):
            blocks.append({
                "type": "section",
                "text": {"type": "mrkdwn", "text": f"*🔗 Pattern:* {correlation['description']}"}
            })
        
        blocks.append({"type": "divider"})
        blocks.append({
            "type": "section",
            "text": {"type": "mrkdwn", "text": f"*🤖 AI:*\n{analysis[:2800]}"}
        })
        
        try:
            response = requests.post(self.slack_webhook, json={"blocks": blocks}, timeout=5)
            if response.status_code == 200:
                print(f"💬 Sent to Slack!")
            else:
                print(f"❌ Slack error: {response.status_code}")
        except Exception as e:
            print(f"❌ Slack failed: {e}")
    
    def format_alert_report(self, alert: Dict, analysis: str, cost: float, 
                          anomalies: List[Dict] = None, correlation: Dict = None) -> str:
        """Format report"""
        alert_name = alert['labels'].get('alertname', 'Unknown')
        severity = alert['labels'].get('severity', 'unknown')
        
        report = f"""
{'='*80}
🚨 ALERT ANALYSIS
{'='*80}

Alert: {alert_name}
Severity: {severity}
Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
Cost: ${cost:.6f}
"""
        
        if anomalies:
            report += f"\n{'-'*80}\n🔍 ANOMALIES\n{'-'*80}\n\n"
            for a in anomalies:
                report += f"{a['metric']}: {a['current']:.4f} (baseline: {a['baseline']:.4f}, z: {a['z_score']:.2f})\n"
        
        if correlation and correlation.get('correlated'):
            report += f"\n{'-'*80}\n🔗 CORRELATION\n{'-'*80}\n"
            report += f"{correlation['description']}\n"
        
        report += f"\n{'-'*80}\n🤖 AI ANALYSIS\n{'-'*80}\n\n{analysis}\n\n{'='*80}\n"
        return report
    
    def monitor_and_analyze(self, interval: int = 30):
        """Main loop - FIXED: Better deduplication!"""
        print("🚀 Enhanced Alert Analyzer Started!")
        print(f"{'='*80}\n")
        
        iteration = 0
        alert_states = {}  # Track: {alert_name: 'firing' | 'resolved'}
        
        while True:
            try:
                iteration += 1
                timestamp = datetime.now().strftime('%H:%M:%S')
                
                # Check anomalies
                anomalies = self.detect_anomalies()
                if anomalies:
                    print(f"🔍 [{timestamp}] {len(anomalies)} anomalies")
                
                # Get alerts
                alerts = self.get_active_alerts()
                current_alert_names = {a['labels'].get('alertname') for a in alerts}
                
                if not alerts:
                    print(f"✅ [{timestamp}] Iteration {iteration}: No alerts")
                    alert_states.clear()  # Clear when no alerts
                else:
                    print(f"🔥 [{timestamp}] Iteration {iteration}: {len(alerts)} alert(s)")
                    
                    correlation = self.correlate_alerts(alerts)
                    if correlation.get('correlated'):
                        print(f"🔗 {correlation['description']}")
                    
                    for alert in alerts:
                        alert_name = alert['labels'].get('alertname')
                        
                        # DEDUPLICATION: Only analyze if NEW or was resolved before
                        if alert_name in alert_states and alert_states[alert_name] == 'firing':
                            # Already analyzed and still firing - SKIP!
                            continue
                        
                        # NEW or RE-FIRING - analyze it!
                        print(f"\n🆕 NEW: {alert_name}")
                        alert_states[alert_name] = 'firing'
                        
                        analysis, cost = self.analyze_alert_with_ai(alert, anomalies, correlation)
                        report = self.format_alert_report(alert, analysis, cost, anomalies, correlation)
                        print(report)
                        
                        self.send_to_slack(alert, analysis, anomalies, correlation)
                        
                        # Save
                        filename = f"alert_{alert_name}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
                        try:
                            with open(filename, 'w') as f:
                                f.write(report)
                            print(f"💾 Saved: {filename}\n")
                        except Exception as e:
                            print(f"❌ Save failed: {e}\n")
                        
                        self.analyzed_alerts.add(alert_name)
                        self.alert_history.append({
                            'alert': alert,
                            'timestamp': datetime.now(),
                            'analysis': analysis
                        })
                    
                    # Mark resolved alerts
                    for prev_alert in list(alert_states.keys()):
                        if prev_alert not in current_alert_names:
                            print(f"✅ Resolved: {prev_alert}")
                            del alert_states[prev_alert]
                
                time.sleep(interval)
                
            except KeyboardInterrupt:
                print(f"\n\n{'='*80}")
                print("👋 Shutting down...")
                print(f"💰 Total: ${self.total_cost:.6f}")
                print(f"📊 Analyzed: {len(self.analyzed_alerts)}")
                print(f"{'='*80}\n")
                break
            except Exception as e:
                print(f"❌ Error: {e}")
                time.sleep(interval)


def main():
    openai_key = os.getenv('OPENAI_API_KEY')
    if not openai_key:
        print("❌ OPENAI_API_KEY not set!")
        return
    
    slack_webhook = os.getenv('SLACK_WEBHOOK_URL')
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