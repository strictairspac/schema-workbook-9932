ROLES = ('admin', 'operator', 'viewer')
RUN_STATES = ('queued', 'running', 'completed', 'failed')
# 方案核验状态：待核验 -> 无损 / 有损 / 已过期
PLAN_STATES = ('queued', 'running', 'lossless', 'lossy', 'stale')
PLAN_QUEUE = 'schemaworkbook:plan-queue'
