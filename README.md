# djangoFlex: Your Django Supercharger 🚀

Welcome to djangoFlex, the Django framework template that puts flexibility at your fingertips! Whether you're building a simple web app or a complex microservices architecture, djangoFlex has got you covered.

## 🌟 What's in the Box?

djangoFlex comes pre-loaded with a smorgasbord of goodies:

1. 🐰 **RabbitMQ**: Message queuing made easy!
2. 📹 **SRS (Simple RTMP Server)**: For your streaming needs.
3. 🐘 **PostgreSQL**: Robust relational database.
4. 🔄 **Redis**: In-memory data structure store.

## 🚀 Quick Start

1. Clone this repository:
   ```
   git clone https://github.com/yourusername/djangoFlex.git
   cd djangoFlex
   ```

2. Create a new Conda environment with Python 3.12:
   ```
   conda create --name djangoFlex python=3.12
   ```

3. Activate the environment:
   ```
   conda activate djangoFlex
   ```

4. Install the dependencies:
   ```
   pip install -r requirements.txt
   ```

5. Set up your environment variables:
   ```
   cp .env.example .env
   ```
   Edit `.env` to configure your settings.

6. Start the Docker containers:
   ```
   docker-compose up -d
   ```

7. Apply database migrations:
   ```
   python manage.py migrate
   ```

8. Create a superuser:
   ```
   python manage.py createsuperuser
   ```

9. Run the Django development server:
   ```
   python manage.py runserver
   ```

10. Visit `http://127.0.0.1:8000/` to see your djangoFlex project in action!

## 🎛 Service Details

### RabbitMQ
- Management UI: `http://localhost:15676` (default credentials: guest/guest)
- AMQP port: 5675

### SRS (Simple RTMP Server)
- RTMP port: 1935
- HTTP port: 8080

### PostgreSQL
- Port: 5435
- Default database: your_postgres_database
- Default user: postgres

### Redis
- Port: 6399

## 🛠 Customization

You can customize the services by editing the `docker-compose.yml` file and the corresponding environment variables in your `.env` file.

## 🌈 Features

- 🏗 Pre-configured Django project structure
- 🔐 Environment-based settings
- 🐳 Docker integration for easy service management
- 📚 Swagger API documentation (available at `/swagger/`)
- 🔗 Sensible URL configuration

## 🎨 Adding Your Own Apps

1. Create a new Django app:
   ```
   python manage.py startapp myawesome_app
   ```

2. Add your new app to `INSTALLED_APPS` in `djangoFlex/settings.py`.

3. Develop your views, models, and URLs.

4. Include your app's URLs in `djangoFlex/urls.py`.

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