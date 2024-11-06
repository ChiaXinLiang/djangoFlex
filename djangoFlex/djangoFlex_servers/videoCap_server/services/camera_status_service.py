from ..models import CameraList

class CameraStatusService:
    @staticmethod
    def update_camera_status(rtmp_url, status):
        CameraList.objects.filter(camera_url=rtmp_url).update(camera_status=status)

    @staticmethod
    def get_camera_status(rtmp_url):
        camera = CameraList.objects.filter(camera_url=rtmp_url).first()
        return camera.camera_status if camera else False
