from vstools import vs, core, clip_async_render
import os
import pandas as pd


def validate_format(input: vs.VideoNode, formats: tuple[int, ...] | int):
    if isinstance(formats, int):
        formats = (formats,)

    fmts = [fmt.name for fmt in formats] # type: ignore

    if input.format.id not in formats: # type: ignore
        raise ValueError(f"Expected {fmts} but got {input.format.name}") # type: ignore


class BaseUtil:
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


class MetricVideoNode:
    def __init__(self, clip: vs.VideoNode, metric):
        self._clip: vs.VideoNode = clip
        self._metric = metric
        self._data: pd.DataFrame | None = None

    def name(self):
        return self.__class__.__name__

    def write_csv(self, filepath, overwrite=False, exclusive: bool = False) -> None:
        file_path = os.path.abspath(filepath)

        if os.path.exists(file_path) and not overwrite:
            if self._data is None:
                self._data = pd.read_csv(file_path)
            return

        if self._data is None:
            self._collect_data()

        self._data.to_csv(file_path, index_label='Frame', index=True)

    def print_statistics(self):
        """
        Automatically calculate and print the statistics for all configured properties.
        """

        if self._data is None:
            self._collect_data()

        if not hasattr(self._metric, 'props') or not self._metric.props:
            raise ValueError("Metric properties not configured.")

        for column_name in self._metric.props:
            if column_name not in self._data.columns:
                raise ValueError(f"Column '{column_name}' not found in the data.")
            print(f"Statistics for {column_name}:")
            mean_val = self._data[column_name].mean()
            median_val = self._data[column_name].median()
            std_dev_val = self._data[column_name].std()
            percentile_5th_val = self._data[column_name].quantile(0.05)
            percentile_95th_val = self._data[column_name].quantile(0.95)

            # Print the formatted statistics
            print(f"Mean: {mean_val}")
            print(f"Median: {median_val}")
            print(f"Std Dev: {std_dev_val}")
            print(f"5th Percentile: {percentile_5th_val}")
            print(f"95th Percentile: {percentile_95th_val}\n")

    def plot(self, props: str = None, normalize: bool = False, scale_relative: bool = False) -> None:
        import matplotlib.pyplot as plt
        
        if self._data is None:
            self._collect_data()

        frames = range(len(self._data))
    
        if props is None:
            props = self._metric.props

        fig, ax1 = plt.subplots()
    
        for prop in props:
            metric_values = self._data[prop]
    
            if prop.startswith("_"):
                prop = prop[1:]
    
            ax1.plot(frames, metric_values, label=prop)
    
        ax1.set_xlabel('Frame')
        ax1.set_ylabel('Metric Value')
        ax1.grid(True)
        ax1.legend(loc='upper left')
    
        if normalize or scale_relative:
            ax2 = ax1.twinx()
            for prop in props:
                metric_values = self._data[prop]
    
                if normalize:
                    metric_values = (metric_values - metric_values.min()) / (metric_values.max() - metric_values.min())
    
                if scale_relative:
                    metric_values = metric_values / metric_values.max()
    
                ax2.plot(frames, metric_values, linestyle='--', alpha=0.7)
    
            if normalize:
                ax2.set_ylabel('Normalized Scale (0.0 to 1.0)')
            elif scale_relative:
                ax2.set_ylabel('Relative Scale (0.0 to 1.0)')
    
            ax2.set_ylim(0, 1)
    
        title = f'{self._metric.__class__.__name__} Metric'
        if normalize:
            title += ' (Normalized)'
        if scale_relative:
            title += ' (Relative Scale)'
            

        plt.title(title)

        plt.tight_layout()
        plt.show()
        
    def _collect_data(self):

        self._data = clip_async_render(
            clip=self._clip,
            outfile=None,
            progress='Getting frame props...',
            callback=lambda _, f: f.props.copy(),
            async_requests=1
        ) # type: ignore

        self._data = pd.DataFrame(self._data)

    def __getattr__(self, name):
        return getattr(self._clip, name)