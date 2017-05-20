"""Converts between the RGB and CAM02-UCS color spaces."""

from collections import namedtuple
from functools import partial

import colour
from colour.utilities import tsplit, tstack
import numpy as np
from scipy.optimize import fmin_l_bfgs_b

Conditions = namedtuple('Conditions', 'Y_w L_A Y_b surround')
DARK_BG = Conditions(80, 16, 0.8, colour.CIECAM02_VIEWING_CONDITIONS['Average'])
NEUTRAL_BG = Conditions(80, 16, 16, colour.CIECAM02_VIEWING_CONDITIONS['Average'])
LIGHT_BG = Conditions(80, 16, 80, colour.CIECAM02_VIEWING_CONDITIONS['Average'])


def get_conds(bg='neutral'):
    bg = bg.lower()
    if bg == 'dark':
        return DARK_BG
    if bg == 'light':
        return LIGHT_BG
    return NEUTRAL_BG


def apow(x, power):
    """Raises x to the given power, treating negative numbers in a mirrored fashion."""
    return np.abs(x)**power * np.sign(x)


RGB_CS = colour.RGB_Colourspace('rgb',
                                colour.sRGB_COLOURSPACE.primaries,
                                colour.sRGB_COLOURSPACE.whitepoint,
                                encoding_cctf=partial(apow, power=1/2.2),
                                decoding_cctf=partial(apow, power=2.2),
                                use_derived_RGB_to_XYZ_matrix=True,
                                use_derived_XYZ_to_RGB_matrix=True)


def rgb_to_XYZ(RGB):
    """Converts from the RGB colorspace to XYZ tristimulus values."""
    return colour.RGB_to_XYZ(RGB, RGB_CS.whitepoint, RGB_CS.whitepoint,
                             RGB_CS.RGB_to_XYZ_matrix, decoding_cctf=RGB_CS.decoding_cctf)


def XYZ_to_rgb(XYZ):
    """Converts from XYZ tristimulus values to the RGB colorspace."""
    return colour.XYZ_to_RGB(XYZ, RGB_CS.whitepoint, RGB_CS.whitepoint,
                             RGB_CS.XYZ_to_RGB_matrix, encoding_cctf=RGB_CS.encoding_cctf)


def rgb_to_ucs(RGB, conds):
    """Converts from the RGB colorspace to CAM02-UCS."""
    XYZ = rgb_to_XYZ(RGB)
    XYZ_w = rgb_to_XYZ([1, 1, 1])
    Y_w, L_A, Y_b, surround = conds
    cam02 = colour.XYZ_to_CIECAM02(XYZ * Y_w, XYZ_w * Y_w, L_A, Y_b, surround)
    JMh = tstack([cam02.J, cam02.M, cam02.h])
    return colour.models.JMh_CIECAM02_to_CAM02UCS(JMh)


def ucs_to_rgb(Jab, conds):
    """Converts from CAM02-UCS to the RGB colorspace."""
    JMh = colour.models.CAM02UCS_to_JMh_CIECAM02(Jab)
    XYZ_w = rgb_to_XYZ([1, 1, 1])
    Y_w, L_A, Y_b, surround = conds
    XYZ = colour.CIECAM02_to_XYZ(*tsplit(JMh), XYZ_w * Y_w, L_A, Y_b, surround,
                                 input_correlates='JMh') / Y_w
    return XYZ_to_rgb(XYZ)


def constrain_to_gamut(rgb, conds):
    """Constrains the given RGB colorspace color to lie within the RGB colorspace gamut,
    minimizing the CAM02-UCS distance between the input out-of-gamut color and the output in-gamut
    color."""
    x = np.clip(rgb, 0, 1)
    if (rgb == x).all():
        return x
    Jab = rgb_to_ucs(rgb, conds)
    def loss(rgb_):
        return np.sum(np.square(Jab - rgb_to_ucs(rgb_, conds)))
    x_opt, _, _ = fmin_l_bfgs_b(loss, x, approx_grad=True, bounds=[(0, 1)]*3)
    return x_opt


def translate(fg, cond_src, cond_dst, invert_J=False, J_factor=1, M_factor=1):
    """Returns a foreground color, intended for use under viewing conditions cond_dst, that appears
    like the given foreground color under viewing conditions cond_src.

    Args:
        fg (array_like): The foreground color RGB colorspace values to translate.
        cond_src (array_like): The source viewing conditions.
        cond_dst (array_like): The destination viewing conditions.
        invert_J (bool): Inverts the output lightness leaving its color alone.
        J_factor (float): Scales output lightness by this factor.
        M_factor (float): Scales output colourfulness by this factor.

    Returns:
        ndarray: The converted foreground color in the rgb colorspace.
    """
    Jab = rgb_to_ucs(fg, cond_src)
    if invert_J:
        Jab[..., 0] = 100 - Jab[..., 0]
    Jab[..., 0] *= J_factor
    Jab[..., 1:] *= M_factor
    rgb = ucs_to_rgb(Jab, cond_dst)
    return constrain_to_gamut(rgb, cond_dst)
