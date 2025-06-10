# async_utils.py

"""
async_utils.py

非同期実行に関するユーティリティ関数・デコレーターを提供するモジュール。
"""

import asyncio
import inspect
from functools import wraps
from typing import Callable


def make_async(func: Callable) -> Callable:
    """
    関数を非同期関数としてラップするデコレーター。

    - 同期関数の場合: asyncio.run_in_executorを利用して非同期化
    - 非同期関数の場合: そのままawait可能な関数として返す

    Args:
        func (Callable): 任意の関数（同期・非同期どちらでも可）

    Returns:
        Callable: 非同期関数として使える関数
    """
    if inspect.iscoroutinefunction(func):

        @wraps(func)
        async def async_wrapper(*args, **kwargs):
            return await func(*args, **kwargs)

        return async_wrapper
    else:

        @wraps(func)
        async def sync_to_async_wrapper(*args, **kwargs):
            loop = asyncio.get_running_loop()
            return await loop.run_in_executor(None, lambda: func(*args, **kwargs))

        return sync_to_async_wrapper


def make_async_task(func: Callable) -> Callable:
    """
    関数を即座にTaskオブジェクトとしてスケジューリングするデコレーター。

    - 非同期関数の場合: create_taskで即タスク化
    - 同期関数の場合: run_in_executorで非同期化しつつタスク化

    Args:
        func (Callable): 任意の関数（同期・非同期どちらでも可）

    Returns:
        Callable: 呼び出し時にasyncio.Taskを返す関数
    """
    if inspect.iscoroutinefunction(func):

        @wraps(func)
        def async_task_wrapper(*args, **kwargs):
            return asyncio.create_task(func(*args, **kwargs))

        return async_task_wrapper
    else:

        @wraps(func)
        def sync_task_wrapper(*args, **kwargs):
            async def _async_func():
                loop = asyncio.get_running_loop()
                return await loop.run_in_executor(None, lambda: func(*args, **kwargs))

            return asyncio.create_task(_async_func())

        return sync_task_wrapper
