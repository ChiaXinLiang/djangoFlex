import os
import subprocess
import threading
import shutil
from ..logs.log_manager import LogManager
from ..exceptions.video_cap_exceptions import VideoCapException
from ..utils.config_loader import ConfigLoader

class HLSStreamService:
    def __init__(self):
        self.logger = LogManager.get_logger(__name__)
        self.stream_processes = {}
        self.config = ConfigLoader.load_config()

    def start_hls_stream(self, rtmp_url, output_dir):
        try:
            hls_output_dir = os.path.join(output_dir, f"{rtmp_url.split('/')[-1]}_hls")
            os.makedirs(hls_output_dir, exist_ok=True)
            hls_output = os.path.join(hls_output_dir, 'index.m3u8')

            ffmpeg_command = self._build_ffmpeg_command(rtmp_url, hls_output)
            process = subprocess.Popen(ffmpeg_command, stderr=subprocess.PIPE, universal_newlines=True)

            self.stream_processes[rtmp_url] = process
            self._start_log_thread(process, rtmp_url)

            return hls_output_dir
        except Exception as e:
            raise VideoCapException(f"啟動 HLS 串流時發生錯誤: {str(e)}")

    def stop_hls_stream(self, rtmp_url):
        if rtmp_url in self.stream_processes:
            process = self.stream_processes[rtmp_url]
            process.terminate()
            process.wait()
            del self.stream_processes[rtmp_url]

    def cleanup_hls_output(self, rtmp_url):
        hls_output_dir = os.path.join(self.config.video_clip_dir, f"{rtmp_url.split('/')[-1]}_hls")
        if os.path.exists(hls_output_dir):
            try:
                shutil.rmtree(hls_output_dir)
            except Exception as e:
                self.logger.error(f"刪除目錄 {hls_output_dir} 時發生錯誤: {str(e)}")

    def _build_ffmpeg_command(self, rtmp_url, hls_output):
        return [
            'ffmpeg',
            '-y',
            '-i', rtmp_url,
            '-c:v', 'libx264',
            '-preset', 'ultrafast',
            '-tune', 'zerolatency',
            '-r', str(self.config.fps),
            '-g', str(self.config.gop_length),
            '-keyint_min', str(self.config.gop_length),
            '-force_key_frames', f"expr:if(isnan(prev_forced_n),1,eq(n,prev_forced_n+{self.config.gop_length}))",
            '-s', f'{self.config.resolution[0]}x{self.config.resolution[1]}',
            '-f', 'hls',
            '-hls_time', str(self.config.hls_time),
            '-hls_segment_type', 'mpegts',
            '-hls_flags', 'independent_segments',
            '-strftime', '1',
            '-strftime_mkdir', '1',
            '-hls_segment_filename', os.path.join(os.path.dirname(hls_output), '%Y%m%d%H%M_%s.ts'),
            '-loglevel', 'warning',
            '-err_detect', 'ignore_err',
            hls_output
        ]

    def _start_log_thread(self, process, rtmp_url):
        def log_stderr(stderr):
            for line in iter(stderr.readline, ''):
                if line.strip():
                    self.logger.warning(f"FFmpeg ({rtmp_url}): {line.strip()}")

        threading.Thread(target=log_stderr, args=(process.stderr,), daemon=True).start()
