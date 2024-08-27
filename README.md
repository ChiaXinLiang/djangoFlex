# djangoFlex
A Django Framework Template for Flexibility

## Provided Apps

The djangoFlex template includes the following apps:

1. **rabbitmq_client_app**: Utilities and views for RabbitMQ interactions.
   - `send_message_view`: Send a message to a RabbitMQ queue.
   - `receive_message_view`: Receive a message from a RabbitMQ queue.

2. **rabbitmq_server_app**: Server-side setup and configurations for RabbitMQ.
   - Start and manage the RabbitMQ server using provided configuration files.


## Overview

djangoFlex is a template project for Django, designed to provide a quick start for various web applications. It sets up a basic Django project structure with some common configurations and instructions for adding your own apps.

## Getting Started

### 1. Set Up the Environment

1. Clone the djangoFlex repository:
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

4. Install the required packages:
   ```
   pip install -r requirements.txt
   ```

### 2. Configure the Project

1. Rename the sample environment file and update the variables:
   ```
   cp .env.example .env
   ```
   Edit the `.env` file with your specific settings.

2. Apply the initial migrations:
   ```
   python manage.py migrate
   ```

3. Create a superuser (admin):
   ```
   python manage.py createsuperuser
   ```

### 3. Run the Development Server

1. Start the Django development server:
   ```
   python manage.py runserver
   ```

2. Open your web browser and go to `http://127.0.0.1:8000/` to see your Django project in action.

3. Open your web browser and go to `http://127.0.0.1:8000/swagger/` to see the Swagger documentation for your Django project.



## Adding Your Own App

1. Create a new Django app:
   ```
   python manage.py startapp myapp
   ```

2. Add the new app to `INSTALLED_APPS` in `djangoFlex/settings.py`:
   ```python
   INSTALLED_APPS = [
       ...
       'myapp',
   ]
   ```

3. Create views in `myapp/views.py`.

4. Create URL patterns in `myapp/urls.py`.

5. Include the app's URLs in `djangoFlex/urls.py`:
   ```python
   urlpatterns = [
       ...
       path('myapp/', include('myapp.urls')),
   ]
   ```

6. Create and apply migrations for your new app:
   ```
   python manage.py makemigrations myapp
   python manage.py migrate
   ```

## Features

- Pre-configured Django project structure
- Environment-based settings using python-decouple
- Basic URL configuration
- Instructions for adding new apps

## Customization

Feel free to modify any part of the project to suit your needs. The `djangoFlex` directory contains the main project settings and URL configurations.

## Contributing

Contributions to improve djangoFlex are welcome. Please follow these steps:
1. Fork the repository
2. Create a new branch for your feature
3. Commit your changes
4. Push to your fork
5. Submit a pull request

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.