from ...videoCap_server.models import VideoCapConfig

class ConfigurationService:
    def __init__(self):
        self.configs = {}
        self._load_configs()

    def _load_configs(self):
        try:
            for config in VideoCapConfig.objects.filter(is_active=True):
                self.configs[config.rtmp_url] = {
                    'rtmp_url': config.rtmp_url,
                    'output_url': f"rtmp://localhost/live/result_{config.rtmp_url.split('/')[-1]}",
                    'is_active': True,
                    'fps': 15,
                    'frame_size': (1280, 720)
                }
        except Exception as e:
            pass

    def get_config(self, rtmp_url):
        return self.configs.get(rtmp_url)
