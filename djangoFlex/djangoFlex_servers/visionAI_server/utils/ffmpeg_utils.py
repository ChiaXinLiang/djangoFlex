import subprocess

def create_ffmpeg_process(output_url, fps, frame_size):
    """
    創建 FFmpeg 進程用於視頻流處理。

    Args:
        output_url (str): 輸出視頻流的 URL。
        fps (int): 幀率。
        frame_size (tuple): 幀大小，格式為 (width, height)。

    Returns:
        tuple: 包含 FFmpeg 進程對象和檢查進程狀態的函數。

    Raises:
        Exception: 如果創建進程時發生錯誤。
    """
    print(f"output_url: {output_url}")
    try:
        ffmpeg_command = [
            'ffmpeg',
            '-f', 'rawvideo',
            '-vcodec', 'rawvideo',
            '-pix_fmt', 'bgr24',
            '-s', f'{frame_size[0]}x{frame_size[1]}',
            '-r', str(fps),
            '-i', '-',
            '-c:v', 'libx264',
            '-pix_fmt', 'yuv420p',
            '-preset', 'ultrafast',
            '-tune', 'zerolatency',
            '-profile:v', 'baseline',
            '-level', '3.0',
            '-f', 'flv',
            '-max_muxing_queue_size', '1024',
            '-g', '30',
            '-keyint_min', '30',
            '-sc_threshold', '0',
            '-b:v', '2500k',
            '-maxrate', '2500k',
            '-bufsize', '5000k',
            output_url
        ]
        process = subprocess.Popen(ffmpeg_command, stdin=subprocess.PIPE)

        def check_process():
            return process.poll() is None

        return process, check_process
    except Exception as e:
        raise

# Add other FFmpeg-related utility functions here
