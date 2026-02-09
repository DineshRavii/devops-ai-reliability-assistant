#!/bin/bash
# Quick deploy script - will be updated as we progress

WEEK=$1

if [ -z "$WEEK" ]; then
    echo "Usage: ./quick-deploy.sh <week-number>"
    echo "Example: ./quick-deploy.sh 1"
    exit 1
fi

echo "🚀 Deploying Week $WEEK resources..."

case $WEEK in
    1)
        echo "Deploying Week 1 - K8s Basics..."
        kubectl apply -f week1-k8s-basics/01-pods/
        kubectl apply -f week1-k8s-basics/02-deployments/
        ;;
    *)
        echo "Week $WEEK not yet implemented"
        ;;
esac
