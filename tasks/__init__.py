from celery import Celery

app = Celery(broker='amqp://', include=['tasks.notification'])
