from vstools import vs

class CAMBI:
    def calculate(
        self, reference: vs.VideoNode,
        window_size: int = 63,
        topk: float = 0.6,
        tvi_threshold: float = 0.019,
        scores: bool = False,
        scaling: float = None
    ) -> vs.VideoNode:

        return reference.akarin.Cambi(
            window_size=window_size,
            topk=topk,
            tvi_threshold=tvi_threshold,
            scores=scores,
            scaling=scaling
            )