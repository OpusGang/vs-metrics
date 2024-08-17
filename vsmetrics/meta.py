from vstools import vs

class MetricBase:
    formats: list[int] = []
    props: list[str] = []

    def __init__(self, **kwargs):
        self.params = kwargs

    def validate_format(self, input: vs.VideoNode) -> None:
        if input.format.id not in self.formats:                              # type: ignore
            fmts = [fmt.name for fmt in self.formats]             # type: ignore
            raise ValueError(f"Expected {fmts} but got {input.format.name}") # type: ignore

    def _generate_props(self, props: list[str], color_family: int, planes: list[int]) -> list[str]:
        if color_family == vs.GRAY:
            return props

        channel_mapping = {
            vs.YUV: ["y", "u", "v"],
            vs.RGB: ["r", "g", "b"],
        }.get(color_family, ["invalid"]) # type: ignore

        if props == ["invalid"]:
            raise ValueError(f"Invalid color format: {color_family}")

        return [f"{prop}_{channel}" for prop in props for i, channel in enumerate(channel_mapping) if i in planes]