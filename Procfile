release: python manage.py migrate
web: gunicorn actions_insider.wsgi --log-file=-
worker: celery -A actions_data worker
beat: celery -A actions_data beat
