from flask import Flask, Response
from prometheus_client import Counter, Histogram, Gauge, generate_latest
import random
import time
import psutil

app = Flask(__name__)

# Metrics
request_count = Counter('app_requests_total', 'Total requests', ['endpoint', 'method'])
request_duration = Histogram('app_request_duration_seconds', 'Request duration', ['endpoint'])
active_requests = Gauge('app_active_requests', 'Active requests')
cpu_usage = Gauge('app_cpu_usage_percent', 'CPU usage')
memory_usage = Gauge('app_memory_usage_bytes', 'Memory usage')

@app.before_request
def before_request():
    active_requests.inc()

@app.after_request
def after_request(response):
    active_requests.dec()
    return response

@app.route('/')
def home():
    request_count.labels(endpoint='/', method='GET').inc()
    with request_duration.labels(endpoint='/').time():
        return "Hello from Metrics App! Try /metrics, /slow, /error, /heavy"

@app.route('/slow')
def slow():
    request_count.labels(endpoint='/slow', method='GET').inc()
    with request_duration.labels(endpoint='/slow').time():
        delay = random.uniform(1.0, 3.0)
        time.sleep(delay)
        return f"Slept for {delay:.2f} seconds"

@app.route('/error')
def error():
    request_count.labels(endpoint='/error', method='GET').inc()
    return "Intentional error!", 500

@app.route('/heavy')
def heavy():
    request_count.labels(endpoint='/heavy', method='GET').inc()
    with request_duration.labels(endpoint='/heavy').time():
        # Simulate CPU work
        result = sum([i**2 for i in range(100000)])
        return f"Heavy computation done: {result}"

@app.route('/metrics')
def metrics():
    # Update system metrics
    cpu_usage.set(psutil.cpu_percent())
    memory_usage.set(psutil.Process().memory_info().rss)
    return Response(generate_latest(), mimetype='text/plain')

@app.route('/health')
def health():
    return {"status": "healthy"}, 200

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8080)
```

**Create:** `requirements.txt`
```
flask==3.0.0
prometheus-client==0.19.0
psutil==5.9.6