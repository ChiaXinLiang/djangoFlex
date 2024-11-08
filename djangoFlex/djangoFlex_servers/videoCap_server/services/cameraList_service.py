from ..models import CameraList, VideoCapConfig
from django.db import transaction

class CameraListService:
    @staticmethod
    def add_camera(camera_name, camera_url):
        """
        添加新的攝像頭到 CameraList
        """
        camera, created = CameraList.objects.get_or_create(
            camera_url=camera_url,
            defaults={'camera_name': camera_name}
        )
        if created:
            return True, f"Camera '{camera_name}' added successfully."
        else:
            return False, f"Camera with URL '{camera_url}' already exists."

    @staticmethod
    def delete_camera(camera_url):
        """
        從 CameraList 中刪除攝像頭，同時清理相關配置
        """
        try:
            with transaction.atomic():
                camera = CameraList.objects.get(camera_url=camera_url)
                # 刪除相關的 VideoCapConfig
                VideoCapConfig.objects.filter(rtmp_url=camera_url).delete()
                # 刪除 CameraList
                camera.delete()
                return True, f"Camera '{camera.camera_name}' and related configurations deleted successfully."
        except CameraList.DoesNotExist:
            return False, f"Camera with URL '{camera_url}' not found."
        except Exception as e:
            return False, f"Error deleting camera: {str(e)}"

    @staticmethod
    def get_all_cameras():
        """
        獲取所有攝像頭列表
        """
        return CameraList.objects.all()

