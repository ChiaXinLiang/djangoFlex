import subprocess
import os

class VideoCapUtils:
    @staticmethod
    def check_camera_online(rtmp_url, timeout=4):
        try:
            # 檢查是否在 Docker 環境中
            is_docker = os.getenv('IS_DOCKER', 'False') == 'True'
            network_name = os.getenv('NETWORK_NAME', 'djangoflex-network')

            # 如果在 Docker 中，將 localhost 替換為 srs 容器名稱
            input_url = rtmp_url
            if is_docker and 'localhost' in rtmp_url:
                input_url = rtmp_url.replace('localhost', 'srs')
                print(f"[DEBUG] Docker 環境中 ({network_name}): 將 {rtmp_url} 替換為 {input_url}")

            print(f"[DEBUG] 正在檢查攝像頭狀態：{input_url}")
            command = [
                "ffmpeg", "-i", input_url,
                "-t", "2",  # 最多讀取 2 秒
                "-f", "null", "-"  # 不輸出結果
            ]
            print(f"[DEBUG] 執行命令: {' '.join(command)}")

            result = subprocess.run(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=timeout)
            is_online = result.returncode == 0
            print(f"[DEBUG] 攝像頭狀態檢查結果：{'在線' if is_online else '離線'}")
            if not is_online:
                print(f"[DEBUG] FFmpeg 錯誤輸出：{result.stderr.decode()}")
                print(f"[DEBUG] FFmpeg 返回碼：{result.returncode}")
            return is_online
        except subprocess.TimeoutExpired:
            print(f"[DEBUG] 檢查超時：{input_url}")
            return False
        except Exception as e:
            print(f"[DEBUG] FFmpeg 檢測錯誤：{str(e)}")
            print(f"[DEBUG] 異常類型：{type(e)}")
            return False
