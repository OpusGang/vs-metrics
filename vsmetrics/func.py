# find offset
# find desync point

from typing import Any
from vsexprtools import ExprOp, combine
from vskernels import Catrom
from vstools import Matrix, MatrixT, merge_clip_props, vs, core, depth
 
def banding_mask(
    clip: vs.VideoNode,
    scale: int = 2,
    **cambi_args: Any
) -> vs.VideoNode:
    """
    Generates a banding mask from a given video clip.
 
    :param clip         The clip to process.
    :param scale:       The scale factor for the merging operation.
    :param cambi_args:  Additional arguments to be passed to the Cambi filter.
 
    :return:            A banding mask for the input video clip.
    """
 
    cambi_args = dict(topk=0.1, tvi_threshold=0.012) | cambi_args
 
    if clip.format.bits_per_sample > 10:
        clip = depth(clip, 10)
 
    cambi = core.akarin.Cambi(clip, scores=True, **cambi_args)
 
    cambi_masks = [
        Catrom.scale(cambi.std.PropToClip('CAMBI_SCALE%d' % i), clip.width, clip.height)
        for i in range(5)
    ]
 
    banding_mask = combine(
        cambi_masks, ExprOp.ADD, zip(range(1, 6), ExprOp.LOG, ExprOp.MUL),
        expr_suffix=[ExprOp.SQRT, scale, ExprOp.LOG, ExprOp.MUL]
    ).std.Convolution([1, 2, 1, 2, 4, 2, 1, 2, 1])
 
    return merge_clip_props(banding_mask, cambi)