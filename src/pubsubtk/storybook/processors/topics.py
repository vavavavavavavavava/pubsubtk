# storybook/topic.py - Storybook 用 PubSub トピック
"""Storybook 内部で使う PubSub トピック列挙型。"""

from enum import auto

from pubsubtk import AutoNamedTopic


class SBTopic(AutoNamedTopic):
    SELECT_STORY = auto()
    TOGGLE_CANVAS = auto()
