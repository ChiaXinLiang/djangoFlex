
def fps_controller_adjustment(frames, duration, fps):
    """
    調整幀數以匹配目標 FPS，主要用於 2 秒的視頻片段。

    Args:
        frames (list): 原始幀列表。
        duration (float): 視頻持續時間（秒）。
        fps (int): 目標幀率。

    Returns:
        list: 調整後的幀列表。
    """
    target_frame_count = int(duration * fps)
    current_frame_count = len(frames)
    print(f"current_frame_count: {current_frame_count}", f"target_frame_count: {target_frame_count}")

    if current_frame_count == target_frame_count:
        return frames

    if current_frame_count > target_frame_count:
        # 減少幀數
        step = current_frame_count / target_frame_count
        return [frames[int(i * step)] for i in range(target_frame_count)]
    else:
        # 增加幀數
        return frames + [frames[-1]] * (target_frame_count - current_frame_count)

# Add other video-related utility functions here
