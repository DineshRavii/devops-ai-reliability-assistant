# Week 1 - Day 3: Prometheus Installation & Queries

## Date: [12-Feb-2026]

## 🎯 Completed
- [x] Deployed Prometheus to K8s cluster
- [x] Configured Prometheus to scrape metrics-app
- [x] Verified targets showing as UP
- [x] Ran multiple PromQL queries
- [x] Generated traffic and observed metrics in real-time
- [x] Understood time-series data flow

## 📝 Key Learnings

### Prometheus Architecture
- **Pull-based monitoring**: Prometheus scrapes targets
- **Scrape interval**: Every 15 seconds (configurable)
- **Service discovery**: Static configs (later: K8s SD)
- **Storage**: Time-series database (TSDB)

### PromQL Basics
```promql
# Instant vector
app_requests_total

# Rate over time
rate(app_requests_total[5m])

# Aggregation
sum(rate(app_requests_total[5m])) by (endpoint)

# Percentiles
histogram_quantile(0.95, rate(app_request_duration_seconds_bucket[5m]))
```

### Metric Types Understood
- **Counter**: Monotonic increase (requests, errors)
- **Gauge**: Can go up/down (active requests, CPU)
- **Histogram**: Distribution with buckets (latency)

## 🏗️ What I Built
- Prometheus ConfigMap with scrape configs
- Prometheus Deployment (1 replica)
- Prometheus Service (NodePort)
- Successfully scraping metrics-app every 15s

## 💡 Aha Moments
- Prometheus **pulls** metrics, doesn't wait to receive them
- `rate()` is essential for counters - converts cumulative to per-second
- Labels enable powerful filtering and grouping
- Time-series data = metric + labels + value + timestamp

## 📊 Queries I Ran
1. Total requests: `sum(app_requests_total)`
2. Request rate: `rate(app_requests_total[5m])`
3. Error rate: `sum(rate(app_requests_total{status="500"}[5m]))`
4. 95th percentile latency: `histogram_quantile(0.95, ...)`
5. Requests by endpoint: `sum(...) by (endpoint)`

## 🎯 Prometheus Targets
- ✅ prometheus (self-monitoring)
- ✅ metrics-app-service (our app)

## 🔥 Real-Time Monitoring Working!
Generated traffic spikes and watched metrics update every 15s in Prometheus UI.

## 🤔 Questions / To Explore
- How to set up alerts when errors spike?
- How to visualize this better? (Tomorrow: Grafana!)
- Service discovery vs static configs?

## ⏭️ Next: Day 4
Install Grafana and create beautiful dashboards!