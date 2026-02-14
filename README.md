# AI-Powered Incident & Reliability Assistant

**By Dinesh Ravi** | DevOps Engineer | Journey to 50 LPA 🎯

---

## 🚀 Project Overview

Building a production-grade AI-powered monitoring and incident response system from scratch, deployed on Kubernetes, with intelligent alerting and auto-remediation capabilities.

**Goal:** Master DevOps/SRE skills deeply, build impressive portfolio, land Lead DevOps / DevOps Architect role at 50 LPA.

**Timeline:** 12 weeks deep mastery plan

---

## 📊 Current Progress

### ✅ Week 1: Complete Monitoring Stack (DONE!)
- **Day 1:** Kubernetes fundamentals - Pods ✅
- **Day 2:** Built metrics application with Prometheus client ✅
- **Day 3:** Deployed Prometheus, configured scraping ✅
- **Days 4-5:** Alert rules, Grafana dashboards, AlertManager ✅

**Status:** Production-ready monitoring stack operational! 🔥

---

## 🏗️ Architecture
```
┌─────────────────┐
│   Metrics App   │ Flask + Prometheus Client
│  (2 replicas)   │ Exposes /metrics endpoint
└────────┬────────┘
         │
         ↓ (scrape every 15s)
┌─────────────────┐
│   Prometheus    │ Time-series database
│                 │ Alert evaluation
│                 │ PromQL queries
└────┬───────┬────┘
     │       │
     │       └──────→ AlertManager (Alert routing)
     ↓
  Grafana (Dashboards & Visualization)
```

---

## 🛠️ Tech Stack

**Container Orchestration:**
- Kubernetes (Local + KodeKloud labs)
- Docker Desktop

**Monitoring:**
- Prometheus (metrics collection, alerting)
- Grafana (visualization)
- AlertManager (alert routing)

**Application:**
- Python Flask
- Prometheus Client library
- Custom metrics (counters, histograms, gauges)

**Infrastructure as Code:**
- Kubernetes YAML manifests
- ConfigMaps for configuration
- (Terraform coming in Week 3)

**CI/CD:**
- Docker Hub (container registry)
- GitHub (version control)
- (GitHub Actions coming in Week 5)

---

## 📈 Metrics & Alerts

### Application Metrics
- `app_requests_total` - Request counter (by endpoint, method, status)
- `app_request_duration_seconds` - Latency histogram
- `app_active_requests` - Concurrent request gauge
- `app_errors_total` - Error counter
- `app_info` - Application metadata

### Active Alerts
- **HighErrorRate** - Critical when errors > 0.3/sec
- **MetricsAppDown** - Critical when target unreachable
- **HighLatency** - Warning when P95 > 2s
- **LowRequestRate** - Warning when traffic drops
- **AlwaysFiring** - Test alert for pipeline verification

---

## 🎯 Key Achievements

✅ **Dockerized application** pushed to Docker Hub: `dineshravii/metrics-app:v1`

✅ **Kubernetes deployment** with:
- Multi-replica setup (2 pods)
- Health checks (liveness + readiness probes)
- Resource limits
- Service discovery

✅ **Prometheus monitoring** with:
- 15-second scrape interval
- Custom alert rules
- Target health monitoring
- Time-series data storage

✅ **Alert system** with:
- Multiple severity levels
- Configurable thresholds
- Alert grouping
- Firing and resolution tracking

---

## 🧪 Testing & Validation

All alerts tested and verified:
- ✅ Triggered HighErrorRate (300 error requests)
- ✅ Triggered MetricsAppDown (scaled to 0 replicas)
- ✅ Verified alert resolution (scaled back to 2)
- ✅ Confirmed AlertManager receiving alerts

---

## 📂 Repository Structure
```
devops-ai-reliability-assistant/
├── README.md
├── docs/
│   ├── daily-logs/          # Learning journal
│   ├── architecture/         # Diagrams
│   └── screenshots/          # Portfolio evidence
├── week1-k8s-basics/
│   ├── 01-pods/
│   ├── 02-deployments/
│   ├── 03-app/              # Metrics application
│   ├── 04-prometheus/       # Prometheus configs
│   ├── 05-grafana/          # Grafana setup
│   └── 06-alertmanager/     # AlertManager configs
└── scripts/
    └── build-and-push.sh    # CI/CD helpers
```

---

## 🚀 Quick Start

### Prerequisites
- Docker Desktop with Kubernetes enabled
- kubectl configured
- Docker Hub account

### Deploy the Stack
```bash
# Clone repository
git clone https://github.com/dineshravii/devops-ai-reliability-assistant.git
cd devops-ai-reliability-assistant

# Deploy metrics app
kubectl apply -f week1-k8s-basics/03-app/app-deployment.yaml

# Deploy Prometheus
kubectl apply -f week1-k8s-basics/04-prometheus/prometheus-config.yaml
kubectl apply -f week1-k8s-basics/04-prometheus/prometheus-rules.yaml
kubectl apply -f week1-k8s-basics/04-prometheus/prometheus-deployment.yaml

# Access UIs (via NodePort)
kubectl get svc

# Generate test traffic
METRICS_URL="http://localhost:YOUR_NODEPORT"
for i in {1..100}; do curl -s $METRICS_URL/ > /dev/null & done
```

---

## 📚 Learning Resources

**Documentation I Created:**
- Daily learning logs (docs/daily-logs/)
- Architecture decisions
- Troubleshooting guides

**Key Skills Demonstrated:**
- Kubernetes orchestration
- Prometheus monitoring and PromQL
- Alert rule design
- Docker containerization
- Git/GitHub workflow
- Systematic debugging

---

## 🎓 Interview-Ready Topics

**Can confidently discuss:**
- Kubernetes architecture and components
- Prometheus scraping and time-series data
- Alert design and anti-patterns
- Observability best practices (Golden Signals)
- ConfigMap and volume mount patterns
- Service discovery in Kubernetes
- Docker multi-platform builds

---

## 🔜 Next Steps

### Week 2: AI Integration
- Claude API integration
- Intelligent log analysis
- Anomaly detection
- Auto-remediation suggestions

### Week 3-4: AWS & Terraform
- Infrastructure as Code with Terraform
- Deploy to EKS (AWS Kubernetes)
- Production-grade cloud architecture

### Week 5-8: Advanced Features
- CI/CD pipelines
- Security hardening
- Performance optimization
- SRE practices

### Week 9-12: Interview Preparation
- Portfolio polish
- Mock interviews
- Resume optimization
- Job applications

---

## 📞 Connect

**GitHub:** [Your GitHub URL]
**LinkedIn:** [Your LinkedIn URL]
**Docker Hub:** hub.docker.com/u/dineshravii

---

## 📝 License

This project is for educational purposes as part of my DevOps learning journey.

---

**Built with 💪 and ☕ by Dinesh Ravi**

*Last updated: February 16, 2026*