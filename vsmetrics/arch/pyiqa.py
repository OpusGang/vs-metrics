from enum import Enum
from typing import Optional, Callable
import torch
import numpy as np
from pyiqa import create_metric
from vstools import inject_self, vs, core

from ..meta import MetricBase
from ..enums.pyiqa import PyIQAMetric


class PYIQA(MetricBase):
    """
    Reimplementation of https://github.com/pifroggi/vs_iqa

    Image Quality Assessment metrics using PyIQA.
    
    Args:
        metric: Quality assessment metric to use
        ref: Optional reference clip for FR metrics
        fallback: Optional fallback clip when score is outside threshold
        thresh: Threshold value for fallback switching
        thresh_mode: Whether to use fallback when score is lower/higher than threshold
        device: Computation device (CPU/CUDA)
        debug: Whether to overlay debug information on frames
    """

    formats: list[int] = [
        vs.RGBS,
        vs.RGBH
    ]

    props: list[str] = [
        'iqa_score'
    ]

    class Device(Enum):
        CPU = 'cpu'
        CUDA = 'cuda'
    
    class ThreshMode(Enum):
        LOWER = 'lower'
        HIGHER = 'higher'

    Metric = PyIQAMetric
    
    def __init__(
        self,
        metric: Metric | str = Metric.HYPERIQA,
        fallback: Optional[vs.VideoNode] = None,
        thresh: float = 0.5,
        thresh_mode: ThreshMode | str = ThreshMode.LOWER,
        device: Device | str = Device.CPU,
        debug: bool = False
    ):
        self.thresh_mode = thresh_mode.value if isinstance(thresh_mode, self.ThreshMode) else thresh_mode
        self.device = device.value if isinstance(device, self.Device) else device
        
        if isinstance(metric, self.Metric):
            self.metric_name = metric.metric_name
            self.metric_type = metric.metric_type
        else:
            metric_enum = self.Metric.from_string(metric)
            if metric_enum:
                self.metric_name = metric_enum.metric_name
                self.metric_type = metric_enum.metric_type
            else:
                self.metric_name = metric.lower()
                self.metric_type = 'NR'

        self.props = [f'{self.metric_name}_pyiqa']

        self.fallback = fallback
        self.thresh = thresh
        self.debug = debug
        
        self._empty_array = None
        self._tensor_device = torch.device(self.device)
        
        if thresh_mode == self.ThreshMode.LOWER or thresh_mode == 'lower':
            self._should_use_fallback = lambda score: score < thresh
        else:
            self._should_use_fallback = lambda score: score > thresh

    def _init_model(self, fp16: bool) -> tuple[torch.nn.Module, bool]:

        model = create_metric(
            self.metric_name,
            metric_mode=self.metric_type,
            device=self._tensor_device
        )

        if fp16:
            model = model.half()

        return model, model().lower_better

    def _prepare_frame_eval(
        self,
        distorted: vs.VideoNode,
        reference: Optional[vs.VideoNode],
        fp16: bool,
        model: torch.nn.Module,
        lower_better: bool
    ) -> Callable:
        h, w = distorted.height, distorted.width
        self._empty_array = np.empty((h, w, 3), dtype=np.float16 if fp16 else np.float32)
        
        debug_text_prefix = f"({'lower' if lower_better else 'higher'} is better) {self.metric_name} score: "
        debug_text_ref = "\nreference: yes" if reference else "\nreference: no"
        debug_text_fallback = "\nfallback: yes" if self.fallback else "\nfallback: no"

        def frame_to_tensor(frame: vs.VideoFrame) -> torch.Tensor:
            for p in range(frame.format.num_planes):
                self._empty_array[..., p] = np.asarray(frame[p]) # type: ignore
            
            tensor = torch.from_numpy(self._empty_array).to(self._tensor_device)
            tensor.clamp_(0, 1)
            return tensor.permute(2, 0, 1).unsqueeze(0)

        if reference and self.debug:
            def eval_frame(n: int, f: vs.VideoFrame) -> vs.VideoFrame:
                clip_tensor = frame_to_tensor(f)
                ref_tensor = frame_to_tensor(reference.get_frame(n))
                score = model(clip_tensor, ref_tensor).cpu().item()
                
                output_clip = self.fallback if self._should_use_fallback(score) and self.fallback else distorted
                output_clip = core.std.SetFrameProp(output_clip, prop=self.props[0], floatval=score)
                
                if fp16:
                    output_clip = core.resize.Point(output_clip, format=vs.RGBS)
                text = f"{debug_text_prefix}{score:.6f}{debug_text_ref}{debug_text_fallback}"
                output_clip = core.text.Text(output_clip, text, alignment=9, scale=1)
                
                if fp16:
                    output_clip = core.resize.Point(output_clip, format=vs.RGBH)
                
                return output_clip
                
        elif reference:
            def eval_frame(n: int, f: vs.VideoFrame) -> vs.VideoFrame:
                clip_tensor = frame_to_tensor(f)
                ref_tensor = frame_to_tensor(reference.get_frame(n))
                score = model(clip_tensor, ref_tensor).cpu().item()
                output_clip = self.fallback if self._should_use_fallback(score) and self.fallback else distorted
                return core.std.SetFrameProp(output_clip, prop=self.props[0], floatval=score)
                
        elif self.debug:
            def eval_frame(n: int, f: vs.VideoFrame) -> vs.VideoFrame:
                clip_tensor = frame_to_tensor(f)
                score = model(clip_tensor).cpu().item()
                
                output_clip = self.fallback if self._should_use_fallback(score) and self.fallback else distorted
                output_clip = core.std.SetFrameProp(output_clip, prop=self.props[0], floatval=score)
                
                if fp16:
                    output_clip = core.resize.Point(output_clip, format=vs.RGBS)
                text = f"{debug_text_prefix}{score:.6f}{debug_text_ref}{debug_text_fallback}"
                output_clip = core.text.Text(output_clip, text, alignment=9, scale=1)
                if fp16:
                    output_clip = core.resize.Point(output_clip, format=vs.RGBH)
                return output_clip
                
        else:
            def eval_frame(n: int, f: vs.VideoFrame) -> vs.VideoFrame:
                clip_tensor = frame_to_tensor(f)
                score = model(clip_tensor).cpu().item()
                output_clip = self.fallback if self._should_use_fallback(score) and self.fallback else distorted
                return core.std.SetFrameProp(output_clip, prop=self.props[0], floatval=score)

        return eval_frame

    @inject_self
    def calculate(self, distorted: vs.VideoNode, reference: Optional[vs.VideoNode] = None) -> vs.VideoNode:
        self.validate_format(distorted)

        if reference:
            self.validate_format(reference)
            if distorted.width != reference.width or distorted.height != reference.height:
                raise ValueError("Distorted and reference clips must have same dimensions")
            if self.metric_type == 'NR':
                raise ValueError(f"Metric '{self.metric_name}' does not use reference clips (NR)")
        elif self.metric_type == 'FR':
            raise ValueError(f"Metric '{self.metric_name}' requires a reference clip (FR)")

        fp16 = distorted.format.id == vs.RGBH and self.device == 'cuda'
        if fp16 and self.device == 'cpu':
            raise ValueError("RGBH input is only supported on CUDA devices")

        model, lower_better = self._init_model(fp16)
        eval_frame = self._prepare_frame_eval(distorted, reference, fp16, model, lower_better)

        result = core.std.FrameEval(
            distorted,
            eval=eval_frame,
            prop_src=[distorted]
        )

        self._register_metadata(result)
        return result