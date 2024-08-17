from vstools import vs, core

from ..meta import MetricBase

class VMAFMetric(MetricBase):
    props: list[str]
    feature_id: int
    formats: list[int] = [
        vs.YUV410P12,
        vs.YUV420P12,
        vs.YUV422P12,
        vs.YUV444P12
    ]

    def __init__(self):
        if not hasattr(self, 'feature_id') or self.feature_id is None:
            raise ValueError("feature_id must be defined in subclass")

    def calculate(self, reference: vs.VideoNode, distorted: vs.VideoNode) -> vs.VideoNode:
        """
        Calculates the metric score between two video nodes.

        Args:
            reference (vs.VideoNode): The reference video node.
            distorted (vs.VideoNode): The distorted video node.

        Returns:
            distorted (vs.VideoNode) with frame props

        Raises:
            ValueError: If one of the inputs has an unsupported format.
            """

        self.validate_format(reference)
        self.validate_format(distorted)

        clip = core.vmaf.Metric(
            reference=reference, distorted=distorted, feature=self.feature_id  # type: ignore
        )

        return clip