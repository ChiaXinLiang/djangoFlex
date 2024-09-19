import os
from django.apps import AppConfig
class VisionaiServerConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "djangoFlex_servers.visionAI_server"

    def ready(self):
        if os.environ.get('RUN_MAIN', None) != 'true':
            try:
                from .services.drawResult_service import DrawResultService
                from .services.violationDetect_service import ViolationDetectService

                # Stop existing services
                DrawResultService.stop_all_services()
                ViolationDetectService.stop_service()

                # Initialize DrawResultService
                DrawResultService()
                # Initialize ViolationDetectService
                ViolationDetectService()

                print("Vision AI服务已停止并重新初始化完成！")
            except Exception as e:
                print(f"Vision AI服务初始化过程中发生错误: {str(e)}")
