# In your_app/management/commands/check_threads.py
from django.core.management.base import BaseCommand
from djangoFlex_servers.videoCap_server.services.videoCap_service import VideoCapService

class Command(BaseCommand):
    help = 'Check running video capture threads'

    def handle(self, *args, **options):
        video_cap_service = VideoCapService()
        running_threads = video_cap_service.list_running_threads()
        for thread in running_threads:
            self.stdout.write(self.style.SUCCESS(
                f"Thread for {thread['rtmp_url']}: ID={thread['thread_id']}, Name={thread['thread_name']}, Is Alive={thread['is_alive']}"
            ))