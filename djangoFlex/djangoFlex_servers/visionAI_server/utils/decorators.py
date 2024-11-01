import time
import random
from functools import wraps

def retry_with_backoff(retries=5, backoff_in_seconds=1):
    """
    裝飾器：使用指數退避策略重試失敗的函數。

    Args:
        retries (int): 最大重試次數。
        backoff_in_seconds (int): 初始退避時間（秒）。

    Returns:
        function: 裝飾器函數。
    """
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            x = 0
            while True:
                try:
                    return func(*args, **kwargs)
                except Exception as e:
                    if x == retries:
                        raise
                    sleep = backoff_in_seconds * 2 ** x + random.uniform(0, 1)
                    time.sleep(sleep)
                    x += 1
        return wrapper
    return decorator