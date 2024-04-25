# vs-metrics

```sh
pip install git+https://github.com/OpusGang/vs-metrics.git --no-cache-dir -U
```

```sh
    from vsmetrics import (
        BRISQUE,
        BUTTERAUGLI,
        CAMBI,
        CIEDE2000,
        GLCM,
        GMSD,
        LPIPS,
        MAD,
        MAE,
        MDSI,
        MSSSIM,
        PSNR,
        PSNRHVS,
        RMS,
        RMSE,
        SSIM,
        SSIMULACRA,
        SVD,
        VIF,
        VMAF,
        WADIQAM,
        Blur,
        ColorMap,
        ColormapTypes,
        Correlation,
        Covariance,
        Edge,
        Hash_3117,
        LocaLBinaryPattern,
        Mean,
        StandardDeviation,
        Variance,
        VisualizeDiffs,
    )

from vstools import vs, core, Matrix
from vsrgtools import gauss_blur

src = src[0:100]
src = src.resize.Bicubic(
    width=512,
    height=512,
    format=vs.RGBS,
    matrix_in=Matrix.BT709
)

blur = gauss_blur(src, sigma=1)

metric = BUTTERAUGLI()

compare1 = metric.calculate(src, blur, linear=True)
compare2 = metric.calculate(src, blur.std.Invert(), linear=False)

# generate plots
compare1.plot()
compare2.plot()

# write to CSV
compare2.write_csv("test.csv", overwrite=True)

# basic summary
compare1.print_statistics()

src.set_output()
compare1.set_output(1)
```
