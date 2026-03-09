# Task 5.10 — HPA for backend and workers

**Epic:** [05-production-rollout](../epic.md)

---

## Objective

Horizontal Pod Autoscaler (HPA) for backend and workers; scale workers by queue depth where possible (EDD §10.2).

## Scope

- **Backend HPA:** Scale on CPU and/or memory; min/max replicas; target utilization (e.g. 70% CPU).
- **Workers HPA:** Scale on queue depth (custom metric from Redis or queue) or CPU/memory; min/max replicas (EDD §10.2).
- **Metrics server:** Ensure metrics-server (or custom metrics adapter) is available for HPA.
- **Testing:** Load test to verify scale-up and scale-down; document expected behavior.
- **Cost:** Max replica limits to avoid runaway cost; alert on sustained high replica count.

## Acceptance criteria

- [ ] Backend scales with load; worker count responds to queue depth or CPU/memory.
- [ ] Scale-up and scale-down have been observed under test or production load.
- [ ] Min/max and metrics are documented; alerts on scaling limits if needed.
