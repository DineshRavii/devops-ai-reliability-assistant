#!/usr/bin/env python3
"""
AI-Powered Alert Analyzer using OpenAI GPT-4o-mini
Cost: ~$0.0004 per analysis (very cheap!)
"""

from openai import OpenAI
import requests
import json
import time
import os
from datetime import datetime
from typing import List, Dict, Optional

class AlertAnalyzer:
    def __init__(self, 
                 openai_api_key: str,
                 prometheus_url: str = "http://prometheus:9090",
                 model: str = "gpt-4o-mini"):
        """
        Initialize Alert Analyzer with OpenAI
        
        Args:
            openai_api_key: OpenAI API key
            prometheus_url: Prometheus server URL
            model: OpenAI model to use (gpt-4o-mini is cheapest)
        """
        self.client = OpenAI(api_key=openai_api_key)
        self.prometheus_url = prometheus_url
        self.model = model
        self.analyzed_alerts = set()
        self.total_cost = 0.0
        
        print(f"🤖 Using model: {model}")
        print(f"💰 Estimated cost: $0.0004 per analysis\n")
        
    def get_active_alerts(self) -> List[Dict]:
        """Fetch currently firing alerts from Prometheus"""
        try:
            response = requests.get(
                f"{self.prometheus_url}/api/v1/alerts",
                timeout=5
            )
            response.raise_for_status()
            
            data = response.json()
            if data['status'] != 'success':
                print(f"❌ Prometheus API error: {data}")
                return []
            
            # Filter for firing alerts only
            alerts = data['data']['alerts']
            firing_alerts = [
                alert for alert in alerts 
                if alert['state'] == 'firing'
            ]
            
            return firing_alerts
            
        except requests.exceptions.RequestException as e:
            print(f"❌ Error fetching alerts: {e}")
            return []
    
    def get_metrics_context(self, alert: Dict) -> str:
        """Get relevant metrics for context"""
        try:
            # Get recent error rate
            response = requests.get(
                f"{self.prometheus_url}/api/v1/query",
                params={'query': 'sum(rate(app_requests_total{status="500"}[5m]))'},
                timeout=5
            )
            
            if response.status_code == 200:
                data = response.json()
                if data['status'] == 'success' and data['data']['result']:
                    error_rate = data['data']['result'][0]['value'][1]
                    return f"Current error rate: {error_rate} errors/sec"
            
            return "Metrics unavailable"
            
        except Exception as e:
            return f"Error fetching metrics: {e}"
    
    def analyze_alert_with_ai(self, alert: Dict) -> tuple[str, float]:
        """
        Use OpenAI to analyze the alert
        
        Args:
            alert: Alert data from Prometheus
            
        Returns:
            Tuple of (analysis text, cost in dollars)
        """
        alert_name = alert['labels'].get('alertname', 'Unknown')
        severity = alert['labels'].get('severity', 'unknown')
        description = alert['annotations'].get('description', 'No description')
        summary = alert['annotations'].get('summary', 'No summary')
        
        # Build context
        metrics_context = self.get_metrics_context(alert)
        
        system_prompt = "You are an expert DevOps/SRE engineer with deep knowledge of Kubernetes, Prometheus, and incident response. Provide practical, actionable advice."
        
        user_prompt = f"""Analyze this production alert:

**Alert Details:**
- Name: {alert_name}
- Severity: {severity}
- Summary: {summary}
- Description: {description}
- Active Since: {alert.get('activeAt', 'Unknown')}
- Metrics: {metrics_context}

**Provide:**

1. **Root Cause** (2-3 sentences): What's likely causing this?

2. **Impact** (1-2 sentences): How critical is this? What's affected?

3. **Immediate Actions** (3 specific steps):
   - Include actual kubectl/Prometheus commands where relevant
   - Be specific and actionable

4. **Prevention** (1-2 sentences): How to prevent recurrence?

Keep it concise and practical. Focus on actions, not theory."""

        try:
            print(f"🤖 Analyzing alert '{alert_name}' with {self.model}...")
            
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
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
            
            print(f"✅ Analysis complete!")
            print(f"💰 Cost: ${cost:.6f} | Total session: ${self.total_cost:.6f}")
            
            return analysis, cost
            
        except Exception as e:
            error_msg = f"❌ AI analysis failed: {e}"
            print(error_msg)
            return error_msg, 0.0
    
    def format_alert_report(self, alert: Dict, analysis: str, cost: float) -> str:
        """Format a comprehensive report"""
        alert_name = alert['labels'].get('alertname', 'Unknown')
        severity = alert['labels'].get('severity', 'unknown')
        component = alert['labels'].get('component', 'unknown')
        
        report = f"""
{'='*80}
🚨 ALERT ANALYSIS REPORT
{'='*80}

Alert: {alert_name}
Severity: {severity.upper()}
Component: {component}
Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
Analysis Cost: ${cost:.6f}

{'-'*80}
🤖 AI ANALYSIS (GPT-4o-mini)
{'-'*80}

{analysis}

{'-'*80}
📊 ADDITIONAL INFO
{'-'*80}

Active Since: {alert.get('activeAt', 'Unknown')}
State: {alert.get('state', 'Unknown')}

Full Alert Labels:
{json.dumps(alert.get('labels', {}), indent=2)}

{'='*80}
"""
        return report
    
    def monitor_and_analyze(self, interval: int = 30):
        """
        Continuously monitor alerts and analyze new ones
        
        Args:
            interval: Seconds between checks
        """
        print("🚀 AI-Powered Alert Analyzer Started!")
        print(f"📊 Prometheus: {self.prometheus_url}")
        print(f"🤖 AI Model: {self.model}")
        print(f"⏰ Check interval: {interval} seconds")
        print(f"💰 Running cost tracker enabled")
        print(f"{'='*80}\n")
        
        iteration = 0
        
        while True:
            try:
                iteration += 1
                
                # Get current alerts
                alerts = self.get_active_alerts()
                
                timestamp = datetime.now().strftime('%H:%M:%S')
                
                if not alerts:
                    print(f"✅ [{timestamp}] Iteration {iteration}: No firing alerts")
                else:
                    print(f"🔥 [{timestamp}] Iteration {iteration}: Found {len(alerts)} firing alert(s)")
                    
                    # Analyze each new alert
                    for alert in alerts:
                        alert_id = f"{alert['labels'].get('alertname')}_{alert.get('activeAt')}"
                        
                        # Skip if already analyzed
                        if alert_id in self.analyzed_alerts:
                            print(f"   ⏭️  Skipping already-analyzed: {alert['labels'].get('alertname')}")
                            continue
                        
                        print(f"\n🆕 NEW ALERT DETECTED: {alert['labels'].get('alertname')}")
                        
                        # Analyze with AI
                        analysis, cost = self.analyze_alert_with_ai(alert)
                        
                        # Format and print report
                        report = self.format_alert_report(alert, analysis, cost)
                        print(report)
                        
                        # Save report to file
                        safe_id = alert_id.replace(':', '_').replace('/', '_')
                        filename = f"alert_analysis_{safe_id}.txt"
                        
                        try:
                            with open(filename, 'w') as f:
                                f.write(report)
                            print(f"💾 Report saved: {filename}\n")
                        except Exception as e:
                            print(f"❌ Failed to save report: {e}\n")
                        
                        # Mark as analyzed
                        self.analyzed_alerts.add(alert_id)
                
                # Wait before next check
                time.sleep(interval)
                
            except KeyboardInterrupt:
                print(f"\n\n{'='*80}")
                print("👋 Shutting down Alert Analyzer...")
                print(f"💰 Total session cost: ${self.total_cost:.6f}")
                print(f"📊 Alerts analyzed: {len(self.analyzed_alerts)}")
                print(f"{'='*80}\n")
                break
                
            except Exception as e:
                print(f"❌ Error in monitoring loop: {e}")
                time.sleep(interval)


def main():
    """Main entry point"""
    # Get API key from environment
    api_key = os.getenv('OPENAI_API_KEY')
    if not api_key:
        print("❌ Error: OPENAI_API_KEY environment variable not set!")
        print("\nGet your key from: https://platform.openai.com/api-keys")
        print("Then set it with: export OPENAI_API_KEY='sk-proj-...'")
        return
    
    # Get Prometheus URL from environment or use default
    prometheus_url = os.getenv('PROMETHEUS_URL', 'http://prometheus:9090')
    
    # Create analyzer
    analyzer = AlertAnalyzer(
        openai_api_key=api_key,
        prometheus_url=prometheus_url,
        model="gpt-4o-mini"  # Cheapest, fastest model
    )
    
    # Start monitoring
    analyzer.monitor_and_analyze(interval=30)


if __name__ == '__main__':
    main()
