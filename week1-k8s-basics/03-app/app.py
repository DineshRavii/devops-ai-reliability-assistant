from flask import Flask, Response
from prometheus_client import Counter, Histogram, Gauge, generate_latest, REGISTRY
import random
import time
import os

app = Flask(__name__)

# Metrics
request_count = Counter(
    'app_requests_total', 
    'Total requests', 
    ['endpoint', 'method', 'status']
)
request_duration = Histogram(
    'app_request_duration_seconds', 
    'Request duration',
    ['endpoint']
)
active_requests = Gauge('app_active_requests', 'Active requests')
error_count = Counter('app_errors_total', 'Total errors', ['endpoint'])

app_info = Gauge('app_info', 'Application info', ['version', 'env'])
app_info.labels(version='1.0.0', env=os.getenv('ENV', 'dev')).set(1)

@app.before_request
def before():
    active_requests.inc()

@app.after_request
def after(response):
    active_requests.dec()
    return response

@app.route('/')
def home():
    request_count.labels(endpoint='/', method='GET', status='200').inc()
    with request_duration.labels(endpoint='/').time():
        return """
        <h1>🚀 Metrics App - DevOps AI Project</h1>
        <p><strong>By Dinesh Ravi</strong></p>
        <h2>Available Endpoints:</h2>
        <ul>
            <li><a href="/metrics">/metrics</a> - Prometheus metrics</li>
            <li><a href="/health">/health</a> - Health check</li>
            <li><a href="/slow">/slow</a> - Slow endpoint (1-3s latency)</li>
            <li><a href="/heavy">/heavy</a> - CPU intensive computation</li>
            <li><a href="/error">/error</a> - Returns 500 error</li>
        </ul>
        <p>🔥 Ready for Prometheus scraping!</p>
        """

@app.route('/health')
def health():
    request_count.labels(endpoint='/health', method='GET', status='200').inc()
    return {"status": "healthy", "version": "1.0.0"}, 200

@app.route('/slow')
def slow():
    with request_duration.labels(endpoint='/slow').time():
        delay = random.uniform(1.0, 3.0)
        time.sleep(delay)
        request_count.labels(endpoint='/slow', method='GET', status='200').inc()
        return f"⏱️  Slept for {delay:.2f} seconds\n"

@app.route('/heavy')
def heavy():
    request_count.labels(endpoint='/heavy', method='GET', status='200').inc()
    with request_duration.labels(endpoint='/heavy').time():
        result = sum([i**2 for i in range(500000)])
        return f"💪 Heavy computation done: {result}\n"

@app.route('/error')
def error():
    request_count.labels(endpoint='/error', method='GET', status='500').inc()
    error_count.labels(endpoint='/error').inc()
    return "❌ Internal Server Error", 500

@app.route('/metrics')
def metrics():
    return Response(generate_latest(REGISTRY), mimetype='text/plain')

if __name__ == '__main__':
    print("=" * 60)
    print("🚀 Metrics App - DevOps AI Reliability Project")
    print("👨‍💻 By Dinesh Ravi")
    print("🌐 Starting on http://0.0.0.0:8080")
    print("=" * 60)
    app.run(host='0.0.0.0', port=8080, debug=False)