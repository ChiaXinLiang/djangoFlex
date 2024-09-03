# djangoFlex: Your Django Supercharger 🚀

Welcome to djangoFlex, the Django framework template that puts flexibility at your fingertips! Whether you're building a simple web app or a complex microservices architecture, djangoFlex has got you covered.

## 🌟 What's in the Box?

djangoFlex comes pre-loaded with a smorgasbord of goodies:

1. 🐰 **RabbitMQ Server**: Message queuing made easy!
2. 🧠 **MLflow Server**: Machine learning experiment tracking at your service.
3. 📹 **Video Capture Server**: Stream and capture video like a pro.
4. 🔌 **RabbitMQ Client**: Communicate with RabbitMQ effortlessly.
5. 🎥 **SRS Server**: Simple RTMP Server for your streaming needs.

## 🚀 Quick Start

1. Clone this bad boy:
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

3. Install the goodies:
   ```
   pip install -r requirements.txt
   ```

4. Set up your secret sauce:
   ```
   cp .env.example .env
   ```
   Edit `.env` to your heart's content.

5. Migrate like a boss:
   ```
   python manage.py migrate
   ```

6. Create a superuser (because you're super):
   ```
   python manage.py createsuperuser
   ```

7. Light it up:
   ```
   python manage.py runserver
   ```

8. Visit `http://127.0.0.1:8000/` and bask in the glory of your new djangoFlex project!

## 🎛 Server Control Center

For detailed API documentation, please refer to the Swagger UI at `http://127.0.0.1:8000/swagger/`.

### RabbitMQ
- API: See Swagger UI for RabbitMQ server endpoints
- Dashboard: `http://127.0.0.1:8000/servers/rabbitmq_dashboard/`

### MLflow
- API: See Swagger UI for MLflow server endpoints
- Dashboard: `http://127.0.0.1:8000/servers/mlflow_dashboard/`

### SRS (Simple RTMP Server)
- API: See Swagger UI for SRS server endpoints
- Dashboard: `http://127.0.0.1:8000/servers/srs_dashboard/`

### Video Capture
- API: See Swagger UI for Video Capture server endpoints

## 🛠 Customization

Feel free to tinker with the `djangoFlex/config/servers.yaml` file to bend the servers to your will. The world is your oyster!

## 🌈 Features That'll Make You Smile

- 🏗 Pre-baked Django project structure
- 🔐 Environment-based settings (shhh, it's a secret)
- 📄 YAML-based server configuration (because who doesn't love YAML?)
- 🐳 Docker integration for RabbitMQ and MLflow (containers, assemble!)
- 📹 Video capture service for RTMP streams (lights, camera, action!)
- 📚 Swagger API documentation (because reading is fundamental)
- 🔗 URL configuration that just makes sense

## 🎨 Adding Your Own Flair

1. Spawn a new app:
   ```
   python manage.py startapp myawesome_app
   ```

2. Tell Django about your new creation in `djangoFlex/settings.py`:

3. Craft your views in `myawesome_app/views.py`.

4. Design your URL patterns in `myawesome_app/urls.py`.

5. Plug it into the main URLs in `djangoFlex/urls.py`:

6. Migrate like there's no tomorrow:
   ```
   python manage.py makemigrations myawesome_app
   python manage.py migrate
   ```

## 🤝 Contributing

Got ideas? We love ideas! Here's how to share them:

1. Fork it
2. Branch it
3. Code it
4. Commit it
5. Push it
6. Pull request it

## 📜 License

This project is licensed under the Apache License 2.0. Check out the [LICENSE](LICENSE) file for the legal mumbo jumbo.

Now go forth and build something awesome with djangoFlex! 🚀✨