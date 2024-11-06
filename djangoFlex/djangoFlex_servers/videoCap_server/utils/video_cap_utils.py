import subprocess

class VideoCapUtils:
    @staticmethod
    def check_camera_online(rtmp_url, timeout=4):
        try:
            command = [
                "ffmpeg", "-i", rtmp_url,
                "-t", "2",  # 最多讀取 2 秒
                "-f", "null", "-"  # 不輸出結果
            ]
            result = subprocess.run(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=timeout)
            return result.returncode == 0  # returncode 為 0 表示串流有效
        except subprocess.TimeoutExpired:
            return False
        except Exception as e:
            print(f"FFmpeg 檢測錯誤：{e}")
            return False
