"""
Kubernetes client factory.

Uses the official `kubernetes` Python client. In-cluster config when
running as a pod (service account token auto-mounted at
/var/run/secrets/kubernetes.io/serviceaccount); local kubeconfig when
running outside the cluster (developer laptop, tests).
"""

from __future__ import annotations

import logging
import threading

from kubernetes import client, config
from kubernetes.config.config_exception import ConfigException

logger = logging.getLogger(__name__)

_loaded = False
_load_lock = threading.Lock()


def ensure_loaded() -> bool:
    """Load cluster config once. Returns True if loaded, False if unavailable.

    Thread-safe: FastAPI serves sync handlers from a worker pool, so a cold
    start with concurrent requests would otherwise race through initialization.
    """
    global _loaded
    if _loaded:
        return True
    with _load_lock:
        if _loaded:
            return True
        try:
            config.load_incluster_config()
            logger.info("k8s: using in-cluster config")
            _loaded = True
            return True
        except ConfigException:
            pass
        try:
            config.load_kube_config()
            logger.info("k8s: using local kubeconfig")
            _loaded = True
            return True
        except (ConfigException, FileNotFoundError):
            logger.warning("k8s: no config available; cluster reads will degrade")
            return False


def core_v1() -> client.CoreV1Api:
    ensure_loaded()
    return client.CoreV1Api()


def apps_v1() -> client.AppsV1Api:
    ensure_loaded()
    return client.AppsV1Api()
