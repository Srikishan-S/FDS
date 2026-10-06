def gate(candidate,current,latency,feature_count,stability,memory_mb,confidence,c):
    checks={'improvement':candidate>current+c.min_improvement,'latency':latency<=c.latency_limit_ms,'feature_count':feature_count<=c.max_features,'stability':stability>=c.stability_threshold,'resources':memory_mb<=c.resource_limit_mb,'confidence':confidence>=c.confidence_threshold}
    return all(checks.values()),checks
