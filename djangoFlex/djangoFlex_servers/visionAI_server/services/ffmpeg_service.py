from ..utils.ffmpeg_utils import create_ffmpeg_process
import subprocess

class FFmpegService:
    def __init__(self):
        self.ffmpeg_processes = {}
        self.ffmpeg_checkers = {}

    def start_ffmpeg_process(self, rtmp_url, output_url):
        try:
            self.ffmpeg_processes[rtmp_url], self.ffmpeg_checkers[rtmp_url] = create_ffmpeg_process(output_url, 15, (1280, 720))
        except Exception as e:
            raise

    def stop_ffmpeg_process(self, rtmp_url):
        if rtmp_url in self.ffmpeg_processes:
            try:
                self.ffmpeg_processes[rtmp_url].stdin.close()
                self.ffmpeg_processes[rtmp_url].terminate()
                self.ffmpeg_processes[rtmp_url].wait(timeout=5)
            except subprocess.TimeoutExpired:
                self.ffmpeg_processes[rtmp_url].kill()
            del self.ffmpeg_processes[rtmp_url]
            del self.ffmpeg_checkers[rtmp_url]

    def is_ffmpeg_running(self, rtmp_url):
        return rtmp_url in self.ffmpeg_checkers and self.ffmpeg_checkers[rtmp_url]()

    def write_frame(self, rtmp_url, frame):
        if rtmp_url in self.ffmpeg_processes:
            self.ffmpeg_processes[rtmp_url].stdin.write(frame)
