# alx_travel_app_0x03

### Features
- Asynchronous background processing with Celery + RabbitMQ
- Automatic booking confirmation emails

### Run Instructions
1. Start RabbitMQ: `sudo service rabbitmq-server start`
2. Start Celery: `celery -A alx_travel_app worker --loglevel=info`
3. Run Django: `python manage.py runserver`
