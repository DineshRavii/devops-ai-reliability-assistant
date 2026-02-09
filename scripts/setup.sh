#!/bin/bash
# Quick setup script for KodeKloud labs

echo "🚀 Setting up DevOps AI Project environment..."

# Check if kubectl is available
if ! command -v kubectl &> /dev/null; then
    echo "❌ kubectl not found. Make sure you're in KodeKloud K8s lab"
    exit 1
fi

echo "✅ kubectl found: $(kubectl version --client --short 2>/dev/null || kubectl version --client)"

# Check cluster access
if kubectl cluster-info &> /dev/null; then
    echo "✅ Cluster accessible"
else
    echo "❌ Cannot access cluster"
    exit 1
fi

echo ""
echo "📁 Current directory structure:"
ls -R

echo ""
echo "🎉 Ready to start! Your manifests are ready to apply."
echo ""
echo "Quick commands:"
echo "  kubectl apply -f <manifest.yaml>  # Apply a manifest"
echo "  kubectl get pods                   # List pods"
echo "  kubectl get all                    # See everything"
