import numpy as np

def calculate_iou(box1, box2):
    """
    計算兩個邊界框的交並比（IoU）。

    Args:
        box1 (tuple): 第一個邊界框的坐標 (x1, y1, x2, y2)。
        box2 (tuple): 第二個邊界框的坐標 (x1, y1, x2, y2)。

    Returns:
        float: 兩個邊界框的 IoU 值。
    """
    x1 = max(box1[0], box2[0])
    y1 = max(box1[1], box2[1])
    x2 = min(box1[2], box2[2])
    y2 = min(box1[3], box2[3])

    intersection = max(0, x2 - x1) * max(0, y2 - y1)
    area1 = (box1[2] - box1[0]) * (box1[3] - box1[1])
    area2 = (box2[2] - box2[0]) * (box2[3] - box2[1])
    union = area1 + area2 - intersection

    return intersection / union if union > 0 else 0

def calculate_distance(box1, box2):
    """
    計算兩個邊界框中心點之間的歐氏距離。

    Args:
        box1 (tuple): 第一個邊界框的坐標 (x1, y1, x2, y2)。
        box2 (tuple): 第二個邊界框的坐標 (x1, y1, x2, y2)。

    Returns:
        float: 兩個邊界框中心點之間的距離。
    """
    center1 = np.array([(box1[0] + box1[2]) / 2, (box1[1] + box1[3]) / 2])
    center2 = np.array([(box2[0] + box2[2]) / 2, (box2[1] + box2[3]) / 2])
    return np.linalg.norm(center1 - center2)

def interpolate_detections(first_detections, last_detections, interval):
    """
    在第一幀和最後一幀的檢測結果之間進行插值。

    Args:
        first_detections (list): 第一幀的檢測結果。
        last_detections (list): 最後一幀的檢測結果。
        interval (int): 插值的間隔數。

    Returns:
        list: 插值後的檢測結果列表。
    """
    matched_pairs, unmatched_last = match_detections(first_detections, last_detections)

    interpolated = [[] for _ in range(interval)]

    for i, j in matched_pairs:
        first = first_detections[i]
        last = last_detections[j]
        for k in range(interval):
            weight = (k + 1) / (interval + 1)
            x1 = int(first[0] * (1 - weight) + last[0] * weight)
            y1 = int(first[1] * (1 - weight) + last[1] * weight)
            x2 = int(first[2] * (1 - weight) + last[2] * weight)
            y2 = int(first[3] * (1 - weight) + last[3] * weight)
            interpolated[k].append((x1, y1, x2, y2))

    for j in unmatched_last:
        for k in range(interval):
            interpolated[k].append(last_detections[j])

    return interpolated

def match_detections(first_detections, last_detections):
    """
    匹配第一幀和最後一幀的檢測結果。

    Args:
        first_detections (list): 第一幀的檢測結果。
        last_detections (list): 最後一幀的檢測結果。

    Returns:
        tuple: 包含匹配對和未匹配的最後檢測結果的列表。
    """
    if not first_detections or not last_detections:
        return [], []

    distances = [[calculate_distance(first, last) for last in last_detections] for first in first_detections]
    matched_pairs = []
    unmatched_first = list(range(len(first_detections)))
    unmatched_last = list(range(len(last_detections)))

    while unmatched_first and unmatched_last:
        i, j = min(((i, j) for i in unmatched_first for j in unmatched_last), key=lambda x: distances[x[0]][x[1]])
        matched_pairs.append((i, j))
        unmatched_first.remove(i)
        unmatched_last.remove(j)

    return matched_pairs, unmatched_last

# Add other math-related utility functions here
