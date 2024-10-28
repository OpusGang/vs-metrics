from typing import Callable
from weakref import WeakKeyDictionary
from vstools import vs, split, merge_clip_props

_node_metadata_map = WeakKeyDictionary()

def register_metadata(clip: vs.VideoNode, metadata: dict):
    _node_metadata_map[clip] = metadata

def get_metadata_for_node(clip: vs.VideoNode) -> dict:
    return _node_metadata_map.get(clip, {})


class MetricBase:
    props: list[str] = []
    formats: list[int] = []

    def __init__(self, **kwargs):
        self.params = kwargs

    def validate_format(self, input: vs.VideoNode) -> None:
        if input.format.id not in self.formats:                              # type: ignore
            fmts = [fmt.name for fmt in self.formats]             # type: ignore
            raise ValueError(f"Expected {fmts} but got {input.format.name}") # type: ignore

    def _generate_props(self, props: list[str], color_family: int, planes: list[int]) -> list[str]:
        if color_family == vs.GRAY:
            return props

        # TODO
        # implement GRAY
        channel_mapping = {
            vs.YUV: ["y", "u", "v"],
            vs.RGB: ["r", "g", "b"],
        }.get(color_family, ["invalid"]) # type: ignore

        if props == ["invalid"]:
            raise ValueError(f"Invalid color format: {color_family}")

        return [f"{prop}_{channel}" for prop in props for i, channel in enumerate(channel_mapping) if i in planes]
    
    def _process_planes(
        self, distorted: vs.VideoNode,
        reference: vs.VideoNode,
        planes: list[int],
        func: Callable
    ) -> vs.VideoNode:

        if reference.format.color_family == vs.GRAY:   # type: ignore
            return func(reference, distorted)

        _distorted = split(distorted)
        _reference = split(reference)

        metric = [
            func(_reference[i], _distorted[i], self.props[i])
            if i in planes else _distorted[i]
            for i in range(distorted.format.num_planes)   # type: ignore
        ]

        return merge_clip_props(distorted, *metric)
    
    def _register_metadata(self, clip: vs.VideoNode) -> vs.VideoNode:
        metadata = {
            'metric_name': self.__class__.__name__,
            'props': self.props,
        }
        register_metadata(clip, metadata)
        return clip
