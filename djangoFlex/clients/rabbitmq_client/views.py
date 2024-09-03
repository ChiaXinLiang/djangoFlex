from django.shortcuts import render
from django.views import View

class RabbitMQClientView(View):
    def get(self, request):
        return render(request, 'rabbitmq_client/index.html')
