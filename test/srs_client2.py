import subprocess
import time
import argparse
import os

def stream_to_rtmp(rtmp_url, source_video):
    if not os.path.exists(source_video):
        print(f"Error: Source video file '{source_video}' does not exist.")
        return

    ffmpeg_command = [
        "ffmpeg",
        "-re",
        "-stream_loop", "-1",  # This will repeat 100 times (original + 99 loops)
        "-i", source_video,
        "-c", "copy",
        "-vcodec", "libx264",
        "-preset:v", "ultrafast",
        "-f", "flv",
        rtmp_url
    ]

    try:
        print(f"Starting stream from {source_video} to {rtmp_url}")
        ffmpeg_process = subprocess.Popen(ffmpeg_command, stdout=subprocess.PIPE, stderr=subprocess.PIPE)

        while True:
            output = ffmpeg_process.stderr.readline().decode().strip()
            if output:
                print(output)
            
            if ffmpeg_process.poll() is not None:
                print("Streaming process has ended")
                break

    except KeyboardInterrupt:
        print("Streaming interrupted by user")
    except Exception as e:
        print(f"An error occurred: {str(e)}")
    finally:
        if ffmpeg_process.poll() is None:
            print("Stopping the streaming process")
            ffmpeg_process.terminate()
            ffmpeg_process.wait()

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Stream video to RTMP server')
    parser.add_argument('--rtmp', default="rtmp://localhost/live/livestream2", help='RTMP URL')
    parser.add_argument('--source', default="C:/App/djangoFlex/test/video/outpu9.mp4", help='Source video file')
    args = parser.parse_args()

    stream_to_rtmp(args.rtmp, args.source)
