# djangoFlex: Your Django Supercharger 🚀

Welcome to djangoFlex, a comprehensive Django framework template designed for flexibility and scalability. Whether you're building a simple web app or a complex microservices architecture with video processing and AI capabilities, djangoFlex has got you covered.

## 🌟 What's in the Box?

djangoFlex comes pre-loaded with a smorgasbord of goodies:

1. 🐰 **RabbitMQ**: Message queuing for distributed task management.
2. 📹 **SRS (Simple RTMP Server)**: For video streaming needs.
3. 🐘 **PostgreSQL**: Robust relational database for data persistence.
4. 🔄 **Redis**: In-memory data structure store for caching and real-time operations.
5. 📊 **MLflow**: For machine learning model management and tracking.
6. 🎥 **Video Capture Server**: For multi-camera video capture and processing.
7. 🧠 **Vision AI Server**: For object detection and scene analysis.
8. 🍃 **Celery**: Distributed task queue for background processing.

## 🚀 Quick Start

1. Clone this repository:
   ```
   git clone -b <branch name> https://github.com/yourusername/djangoFlex.git
   cd djangoFlex
   ```

2. Create a new Conda environment with Python 3.12:
   ```
   conda create --name djangoFlex python=3.12
   conda activate djangoFlex
   ```

3. Install the dependencies:
   ```
   pip install -r requirements.txt
   ```

4. Set up your environment variables:
   ```
   cp .env.example .env
   ```
   Edit `.env` to configure your settings.

5. Start the Docker containers:
   ```
   sudo docker-compose -f docker-compose.yml up -d
   ```

6. Apply database migrations:
   ```
   python manage.py makemigrations
   python manage.py migrate
   ```

7. Create a superuser:
   ```
   python manage.py createsuperuser
   ```

8. Run the Django development server:
   ```
   python manage.py runserver
   ```

9. Visit `http://127.0.0.1:8000/admin` to see your djangoFlex project in action!

## 🎛 Service Details

### RabbitMQ
- Management UI: `http://localhost:15676` (default credentials: guest/guest)
- AMQP port: 5675

### SRS (Simple RTMP Server)
- RTMP port: 1935
- RTMP port: 1985
- HTTP port: 8080

### PostgreSQL
- Port: 5435
- Default database: your_postgres_database
- Default user: postgres

### Redis
- Port: 6399

### MLflow
- UI: `http://localhost:5000`

## 🛠 Customization

You can customize the services by editing the `docker-compose.yml` file and the corresponding environment variables in your `.env` file.

## 🌈 Features

- 🏗 Pre-configured Django project structure with modular app design
- 🔐 Environment-based settings for easy configuration management
- 🐳 Docker integration for seamless service management
- 📚 Swagger API documentation (available at `/swagger/`)
- 🔗 RESTful API endpoints for all services
- 📹 Multi-camera video capture and processing capabilities
- 🧠 AI-powered object detection and scene analysis
- 📊 MLflow integration for machine learning model tracking and management
- 🐰 RabbitMQ client for distributed messaging
- 🍃 Celery integration for background task processing

## 🎨 Adding Your Own Apps

1. Create a new Django app in the `djangoFlex_servers` directory:
   ```
   python manage.py startapp myawesome_app djangoFlex_servers/myawesome_app
   ```

2. Add your new app to `INSTALLED_APPS` in `djangoFlex/settings.py`.

3. Develop your views, models, and URLs.

4. Include your app's URLs in `djangoFlex_servers/urls.py`.

5. Apply migrations if you've added models:
   ```
   python manage.py makemigrations myawesome_app
   python manage.py migrate
   ```

## 🤝 Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## 📜 License

This project is licensed under the Apache License 2.0. See the [LICENSE](LICENSE) file for details.

Happy coding with djangoFlex! 🚀✨
