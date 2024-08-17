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
