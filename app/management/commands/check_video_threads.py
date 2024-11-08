from django.core.management.base import BaseCommand
from app.services.video_cap_service import video_cap_service

class Command(BaseCommand):
    help = 'Check and clean up video capture threads'

    def handle(self, *args, **options):
        video_cap_service.check_all_threads()
        self.stdout.write(self.style.SUCCESS('Successfully checked video capture threads'))