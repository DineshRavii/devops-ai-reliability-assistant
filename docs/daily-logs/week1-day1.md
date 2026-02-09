# Week 1 - Day 1: Kubernetes Pods

## Date: [10-Feb-2026]

## 🎯 Goals
- Understand what Pods are
- Create first pod using kubectl
- Create pod using YAML manifest

## 📝 What I Learned
How to write a pod manifest file
How to create it
### Key Concepts
- Creation of pod

### Commands Used
```bash
kubectl apply -f my-first-pod.yaml 
kubectl get pods
kubectl get pods -w
kubectl get pods -o wide
kubectl describe po
kubectl exec -it hello-app -- /bin/sh
kubectl delete pod hello-app
```

## 🏗️ What I Built
- Simple nginx pod

## 🤔 Questions / Confusion
- No confusions so far

## ✅ Achievements
- [x] Created first pod ✅
- [x] Used kubectl describe ✅
- [x]] Wrote YAML manifest ✅

## ⏭️ Tomorrow
- Deployments and Services
