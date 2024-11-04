import subprocess
import time
import argparse
import os
import threading

def stream_to_rtmp(rtmp_url: str, source_video: str) -> None:
    """
    將源影片檔案流式傳輸到指定的RTMP URL。

    此函數使用FFmpeg將影片檔案以流的形式傳輸到RTMP服務器。
    它會無限循環播放影片，直到用戶中斷或發生錯誤。

    參數:
    rtmp_url (str): 目標RTMP服務器的URL。
    source_video (str): 源影片檔案的路徑。

    返回:
    None
    """
    if not os.path.exists(source_video):
        print(f"錯誤：源影片檔案 '{source_video}' 不存在。")
        return

    ffmpeg_command = [
        "ffmpeg",
        "-re",
        "-stream_loop", "-1",  # 這將無限循環重複影片
        "-i", source_video,
        # "-c", "copy",
        "-vcodec", "libx264",
        "-preset:v", "ultrafast",
        "-f", "flv",
        rtmp_url
    ]

    try:
        print(f"開始從 {source_video} 向 {rtmp_url} 傳輸流")
        ffmpeg_process = subprocess.Popen(ffmpeg_command, stdout=subprocess.PIPE, stderr=subprocess.PIPE)

        while True:
            output = ffmpeg_process.stderr.readline().decode().strip()
            if output:
                print(output)

            if ffmpeg_process.poll() is not None:
                print("流傳輸進程已結束")
                break

    except KeyboardInterrupt:
        print("用戶中斷了流傳輸")
    except Exception as e:
        print(f"發生錯誤：{str(e)}")
    finally:
        if ffmpeg_process.poll() is None:
            print("正在停止流傳輸進程")
            ffmpeg_process.terminate()
            ffmpeg_process.wait()

if __name__ == '__main__':
    # 設置命令行參數解析器
    parser = argparse.ArgumentParser(description='將影片流傳輸到RTMP服務器')
    parser.add_argument('--rtmp1', default="rtmp://localhost/live/livestream/1", help='RTMP URL')
    parser.add_argument('--source1', default="./video/outpu6.mp4", help='第一條源影片檔案路徑')

    parser.add_argument('--rtmp2', default="rtmp://localhost/live/livestream/2", help='RTMP URL')
    parser.add_argument('--source2', default="./video/outpu9.mp4", help='第二條源影片檔案路徑')

    args = parser.parse_args()

    # 創建兩個線程來同時進行流傳輸
    thread1 = threading.Thread(target=stream_to_rtmp, args=(args.rtmp1, args.source1))
    thread2 = threading.Thread(target=stream_to_rtmp, args=(args.rtmp2, args.source2))

    # 啟動線程
    thread1.start()
    thread2.start()

    # 等待線程完成
    thread1.join()
    thread2.join()