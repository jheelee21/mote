import numpy as np

from mote.pipeline.signals import tone_signals


def _img(rgb):
    return np.full((32, 32, 3), rgb, dtype=np.uint8)


def test_warm_vs_cool():
    assert tone_signals(_img((230, 150, 60))).warmth > 0.3
    assert tone_signals(_img((40, 70, 160))).warmth < -0.3


def test_grey_is_unsaturated_and_flat():
    s = tone_signals(_img((128, 128, 128)))
    assert s.saturation < 0.01
    assert s.contrast < 0.01
    assert s.palette[0] == "#808080"
