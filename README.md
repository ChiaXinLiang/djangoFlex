# djangoFlex
A Django Framework for Multiple Use

## Getting Started

### 1. Create and Set Up the DjangoFlex Environment

1. Create a new Conda environment with Python 3.12:
   ```
   conda create --name djangoFlex python=3.12
   ```

2. Activate the environment:
   ```
   conda activate djangoFlex
   ```

3. Install the required packages from `requirements.txt`:
   ```
   pip install -r requirements.txt
   ```

### 2. Create the DjangoFlex Project

1. Create a new Django project called DjangoFlex using `django-admin`:
   ```
   django-admin startproject djangoFlex
   ```

### 3. Using the DjangoFlex Project

1. Navigate to the project directory:
   ```
   cd djangoFlex
   ```

2. Create the initial migrations for your database:
   ```
   python manage.py makemigrations
   ```

3. Apply the migrations to set up your database:
   ```
   python manage.py migrate
   ```

4. Run the development server to start using the project:
   ```
   python manage.py runserver
   ```

5. Open your web browser and go to `http://127.0.0.1:8000/` to see your Django project in action.

### 4. Create a Django App

1. Navigate to the project directory if you are not already there:
   ```
   cd djangoFlex
   ```

2. Create a new Django app called `myapp` using the `startapp` command:
   ```
   python manage.py startapp myapp
   ```

3. Add the new app to the `INSTALLED_APPS` list in the `settings.py` file of your Django project:
   ```python
   # djangoFlex/settings.py

   INSTALLED_APPS = [
       ...
       'myapp',
   ]
   ```

4. Create the initial migrations for your new app:
   ```
   python manage.py makemigrations myapp
   ```

5. Apply the migrations to set up the database tables for your new app:
   ```
   python manage.py migrate
   ```

6. Create a view in your new app by editing the `views.py` file:
   ```python
   # myapp/views.py

   from django.http import HttpResponse

   def index(request):
       return HttpResponse("Hello, world. You're at the myapp index.")
   ```

7. Map the view to a URL by editing the `urls.py` file in your new app:
   ```python
   # myapp/urls.py

   from django.urls import path
   from . import views

   urlpatterns = [
       path('', views.index, name='index'),
   ]
   ```

8. Include the app's URL configuration in the project's `urls.py` file:
   ```python
   # djangoFlex/urls.py

   from django.contrib import admin
   from django.urls import include, path

   urlpatterns = [
       path('admin/', admin.site.urls),
       path('myapp/', include('myapp.urls')),
   ]
   ```

9. Run the development server to see your new app in action:
   ```
   python manage.py runserver
   ```

10. Open your web browser and go to `http://127.0.0.1:8000/myapp/` to see the "Hello, world" message from your new app.