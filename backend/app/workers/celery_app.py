import os
from celery import Celery

REDIS_URL = os.getenv("REDIS_URL", "redis://redis:6379/0")
celery_app = Celery("pkb", broker=REDIS_URL, backend=REDIS_URL, include=["app.workers.tasks", "app.workers.quick_tasks"],)

# 配置队列和优先级
celery_app.conf.update(
    task_routes={
        'app.workers.quick_tasks.*': {'queue': 'quick'},
        'app.workers.tasks.classify_content': {'queue': 'classify'},
        'app.workers.tasks.batch_classify_contents': {'queue': 'classify'},
        'app.workers.tasks.generate_embeddings': {'queue': 'heavy'},
        'app.workers.tasks.ingest_file': {'queue': 'ingest'},
        'app.workers.tasks.process_document': {'queue': 'heavy'},
        'app.workers.tasks.process_image_content': {'queue': 'heavy'},
    },
    task_default_queue='default',
    worker_prefetch_multiplier=1,
    task_acks_late=True,
    worker_disable_rate_limits=False,
    task_compression='gzip',
    result_compression='gzip',
)

celery_app.autodiscover_tasks(["app.workers"])

