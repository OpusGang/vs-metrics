from vstools import depth, plane, vs, core, clip_async_render

import os
import polars as pl

from typing import Dict, Union, List, Optional
import numpy as np

from vsmetrics.arch.scenechange.pixelwise import Diff
from vsmetrics.meta import get_metadata_for_node

class DataHandler:
    def __init__(
        self,
        clips: Dict[str, vs.VideoNode] | vs.VideoNode | list[vs.VideoNode],
        csv_path: Optional[str] = None
        ):
        """
        clips: A dictionary where keys are metric names and values are VideoNode clips with frame properties,
               or a single VideoNode, or a list of VideoNodes.
        csv_path: Optional path to a CSV or directory of CSV files for loading precomputed data.
        """
        self.clips = self._normalize_clips(clips)
        self.data: Dict[str, pl.DataFrame] = {}
        self.csv_path = csv_path
        self.frames_to_process: Optional[List[int]] = None

        if csv_path:
            self._read_csv()

    def _normalize_clips(self, clips: Union[Dict[str, vs.VideoNode], vs.VideoNode, List[vs.VideoNode]]) -> Dict[str, vs.VideoNode]:
        if isinstance(clips, dict):
            return clips
        elif isinstance(clips, vs.VideoNode):
            return {self._infer_metric_name(clips): clips}
        elif isinstance(clips, list):
            return {self._infer_metric_name(clip): clip for clip in clips}
        else:
            raise ValueError("Invalid input type for clips. Expected Dict, VideoNode, or List[VideoNode].")

    def _infer_metric_name(self, clip: vs.VideoNode) -> str:
        metadata = get_metadata_for_node(clip)
        metric_name = metadata.get('metric_name', f'unknown_metric_{id(clip)}')
        return metric_name

    def per_scene(self, clip: vs.VideoNode, frames: int = 1) -> None:
        """
        Detects scene changes in the source clip and calculates frames to process for each scene.
        Stores the frame numbers for per-scene metric calculation.

        Args:
            clip (vs.VideoNode): Clip for detecting scene chnages.
            frames (int): The number of frames to collect per scene. Defaults to 1 (midpoint).
        """
        scene_changes = []

        metric = Diff
        # TODO IDEA
        # Add minimum res to class so we can auto-scale to min size
        # sc_clip = SCXVID().calculate(clip.resize.Point(format=vs.YUV420P8))
        sc_clip = metric.calculate(depth(plane(clip, 0), 8).resize.Point(128, 128))

        def _collect_scene_changes(n: int, f):
            if f.props.get(f'{metric.props[0]}', 0) == 1:
                scene_changes.append(n)

        clip_async_render(
            sc_clip,
            progress="Detecting scene changes",
            callback=_collect_scene_changes
        )

        scene_boundaries = [0] + scene_changes + [sc_clip.num_frames - 1]

        self.frames_to_process = []
        for i in range(len(scene_boundaries) - 1):
            start = scene_boundaries[i]
            end = scene_boundaries[i + 1]
            scene_length = end - start

            if frames == 1:
                self.frames_to_process.append((start + end) // 2)
            else:
                for j in range(frames):
                    frame = start + (j * scene_length // (frames - 1))
                    if frame < end:
                        self.frames_to_process.append(frame)

        self.frames_to_process = sorted(list(set(self.frames_to_process)))

    def _collect(self) -> None:
        """Collects metric data from the video clips using weakref"""
        for name, clip in self.clips.items():
            metadata = get_metadata_for_node(clip)
            props = metadata.get('props', [])

            if self.frames_to_process:
                frames = [clip[f:f+1] for f in self.frames_to_process]
                frames_clip = core.std.Splice(frames)
            else:
                frames_clip = clip

            frame_data = clip_async_render(
                clip=frames_clip,
                outfile=None,
                progress=f'Getting frame props for {name}...',
                callback=lambda n, f: {prop: f.props.get(prop) for prop in props},
                async_requests=1
            )

            df = pl.DataFrame(frame_data)
            self.data[name] = df

    def _ensure_data(self):
        if not self.data:
            self._collect()

    def print_statistics(self) -> None:
        """Prints statistical information for each metric in the dataset."""
        self._ensure_data()
    
        for name, df in self.data.items():
            print(f"\nStatistics for {name}:")

            for prop in df.columns:
                stats = df.select([
                    pl.col(prop).mean().alias('Mean'),
                    pl.col(prop).median().alias('Median'),
                    pl.col(prop).std().alias('Std Dev'),
                    pl.col(prop).quantile(0.05).alias('5th Percentile'),
                    pl.col(prop).quantile(0.95).alias('95th Percentile')
                ]).to_dicts()[0]
                
                print(f"\nStatistics for {prop}:")
                for stat_name, value in stats.items():
                    print(f"{stat_name}: {value}")

    def plot_matplotlib(self, normalize: bool = True) -> None:
        import matplotlib.pyplot as plt

        self._ensure_data()
        fig, ax = plt.subplots(figsize=(12, 6))

        for name, df in self.data.items():
            if self.frames_to_process:
                x = self.frames_to_process
            else:
                x = range(len(df))

            for prop in df.columns:
                metric_values = df[prop].to_numpy()

                if normalize:
                    min_val, max_val = metric_values.min(), metric_values.max()
                    if max_val != min_val:
                        metric_values = (metric_values - min_val) / (max_val - min_val)
                    else:
                        metric_values = np.zeros_like(metric_values)  # Or np.ones_like(metric_values)

                ax.plot(x, metric_values, label=f"{name}: {prop}")
                
                if self.frames_to_process:
                    ax.scatter(x, metric_values, marker='o', s=30, zorder=5)

        ax.set_xlabel('Frame')
        ax.set_ylabel('Normalized Metric Value' if normalize else 'Metric Value')
        ax.set_title('Metrics Comparison')
        ax.grid(True)
        ax.legend(loc='center left', bbox_to_anchor=(1, 0.5))

        if self.frames_to_process:
            ax.set_xticks(self.frames_to_process)
            ax.set_xticklabels(self.frames_to_process, rotation=45, ha='right')
        
        if self.frames_to_process:
            ax2 = ax.twiny()
            ax2.set_xlim(ax.get_xlim())
            ax2.set_xticks(self.frames_to_process)
            ax2.set_xticklabels([f"Scene {i+1}" for i in range(len(self.frames_to_process))], rotation=45, ha='left')
            ax2.tick_params(axis='x', which='major', pad=15)

        plt.tight_layout()
        plt.show()

    def plot_pygal(self, normalize: bool = True, output_file: Optional[str] = None) -> None:
        """
        Plots the metrics over time using Pygal
        
        Args:
            normalize (bool): Whether to normalize the metric values. Defaults to True.
            output_file (Optional[str]): File path to save the SVG. If None, the plot will be rendered in the browser.
        """
        import pygal
        from pygal.style import Style   

        self._ensure_data()

        custom_style = Style(
            background='transparent',
            plot_background='transparent',
            foreground='rgba(0, 0, 0, 0.9)',
            foreground_strong='rgba(0, 0, 0, 0.9)',
            foreground_subtle='rgba(0, 0, 0, 0.5)',
            opacity='.6',
            opacity_hover='.9',
            transition='400ms ease-in',
            colors=('#E853A0', '#E8537A', '#E95355', '#E87653', '#E89B53')
        )

        chart = pygal.Line(style=custom_style, x_label_rotation=45, show_minor_x_labels=False)
        chart.title = 'Metrics Comparison'
        chart.x_title = 'Frame'
        chart.y_title = 'Normalized Metric Value' if normalize else 'Metric Value'

        x_labels = self.frames_to_process if self.frames_to_process else list(range(len(next(iter(self.data.values())))))
        chart.x_labels = [str(x) for x in x_labels] # cursed

        for name, df in self.data.items():
            for prop in df.columns:
                metric_values = df[prop].to_numpy()

                if normalize:
                    min_val, max_val = metric_values.min(), metric_values.max()
                    if max_val != min_val:
                        metric_values = (metric_values - min_val) / (max_val - min_val)
                    else:
                        metric_values = np.zeros_like(metric_values)

                chart.add(f"{name}: {prop}", [float(v) for v in metric_values])

        if self.frames_to_process:
            chart.add('Scene Boundaries', 
                      [{'value': float(i), 'node': {'r': 5}} for i, frame in enumerate(self.frames_to_process)], 
                      stroke=False, fill=False, show_dots=True)

        # Render the chart
        if output_file:
            chart.render_to_file(output_file)

    def plot_plotly(self, normalize: bool = True, output_file: Optional[str] = None) -> None:
        """
        Plots the metrics over time using Plotly
        
        Args:
            normalize (bool): Whether to normalize the metric values. Defaults to True.
            output_file (Optional[str]): File path to save the HTML. If None, the plot will be rendered in the browser.
        """
        import plotly.graph_objs as go
        from plotly.subplots import make_subplots

        self._ensure_data()

        fig = make_subplots(specs=[[{"secondary_y": True}]])

        x = self.frames_to_process if self.frames_to_process else list(range(len(next(iter(self.data.values())))))

        for name, df in self.data.items():
            for prop in df.columns:
                metric_values = df[prop].to_numpy()

                if normalize:
                    min_val, max_val = metric_values.min(), metric_values.max()
                    if max_val != min_val:
                        metric_values = (metric_values - min_val) / (max_val - min_val)
                    else:
                        metric_values = np.zeros_like(metric_values)  # Or np.ones_like(metric_values)

                fig.add_trace(
                    go.Scatter(x=x, y=metric_values, name=f"{name}: {prop}", mode='lines+markers')
                )

        # Add scene markers if per-scene processing was used
        #if self.frames_to_process:
        #    fig.add_trace(
        #        go.Scatter(
        #            x=self.frames_to_process,
        #            y=[1] * len(self.frames_to_process),  # Place markers at the top of the plot
        #            mode='markers',
        #            name='Scene Boundaries',
        #            marker=dict(symbol='star', size=10, color='red'),
        #            yaxis='y2'
        #        )
        #    )

        # Update layout
        fig.update_layout(
            title='Metrics Comparison',
            xaxis_title='Frame',
            yaxis_title='Normalized Metric Value' if normalize else 'Metric Value',
            legend=dict(x=1.05, y=1, bordercolor='Black', borderwidth=1),
            hovermode='x unified'
        )

        fig.update_xaxes(tickangle=45)

        fig.update_yaxes(title_text='Metric Value', secondary_y=False)
        fig.update_yaxes(title_text='Scene Boundaries', secondary_y=True, showticklabels=False, range=[0, 1.1])

        if output_file:
            fig.write_html(output_file)
        else:
            fig.show()

    def _read_csv(self):
        if not self.csv_path:
            raise ValueError("CSV path not provided")
        
        if os.path.isfile(self.csv_path):
            self.data["default"] = pl.read_csv(self.csv_path)
        elif os.path.isdir(self.csv_path):
            for file in os.listdir(self.csv_path):
                if file.endswith('.csv'):
                    name = os.path.splitext(file)[0]
                    file_path = os.path.join(self.csv_path, file)
                    self.data[name] = pl.read_csv(file_path)
        else:
            raise FileNotFoundError(f"No CSV file or directory found at {self.csv_path}")
    
    def write(self, filename: str) -> None:
        self._ensure_data()
        
        file_path = os.path.abspath(filename)
        
        if len(self.data) == 1:
            list(self.data.values())[0].write_csv(file_path)
        else:
            dir_path = os.path.splitext(file_path)[0]
            os.makedirs(dir_path, exist_ok=True)
            
            for name, df in self.data.items():
                clip_file_path = os.path.join(dir_path, f"{name}.csv")
                df.write_csv(clip_file_path)
            
            print(f"Data written to directory: {dir_path}")

    def __getattr__(self, name):
        """Fallback for attribute access to return properties from the first clip."""
        return getattr(list(self.clips.values())[0], name)
