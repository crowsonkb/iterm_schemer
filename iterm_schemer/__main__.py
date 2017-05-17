"""Translates iTerm2 color schemes between dark- and light-background."""

from argparse import ArgumentParser, ArgumentDefaultsHelpFormatter, FileType
import plistlib

import numpy as np

from iterm_schemer.cam02ucs import get_conds, rgb_to_ucs, translate

ROWS_INVERT = ['Foreground', 'Background', 'Bold', 'Cursor', 'Cursor Text']
ROWS_INVERT = [k + ' Color' for k in ROWS_INVERT]
ROWS_TRANSLATE = ['Ansi %d Color' % i for i in range(16)] + ROWS_INVERT
COLUMNS = ['Red Component', 'Green Component', 'Blue Component']


def format_rgb(rgb):
    """Formats an RGB color array for display on a 24-bit color terminal."""
    rgb_ = np.uint8(np.round(rgb * 255))
    s = ''
    if rgb_to_ucs(rgb, get_conds())[0] < 30:
        s += '\033[38;2;255;255;255m'
    else:
        s += '\033[38;2;0;0;0m'
    s += '\033[48;2;{};{};{}m'.format(*rgb_)
    s += '[{:>3} {:>3} {:>3}]'.format(*rgb_)
    return s + '\033[0m'


def main():
    """The main function."""
    parser = ArgumentParser(description=__doc__, allow_abbrev=False,
                            formatter_class=ArgumentDefaultsHelpFormatter)
    parser.add_argument('src_scheme', type=FileType('rb'),
                        help='The input iTerm2 color scheme (.itermcolors).')
    parser.add_argument('dst_scheme', type=FileType('wb'),
                        help='The output iTerm2 color scheme (.itermcolors).')
    parser.add_argument('--src-bg', choices=['dark', 'neutral', 'light'], default='neutral',
                        help='The background color type of the input scheme.')
    parser.add_argument('--dst-bg', choices=['dark', 'neutral', 'light'], default='neutral',
                        help='The background color type to translate the input scheme to.')
    parser.add_argument('--invert', action='store_true',
                        help='Invert the foreground, background, bold, cursor, and cursor text '
                             'colors. You probably want this.')
    parser.add_argument('--j-fac', type=float, default=1.0,
                        help='The factor to scale output lightness by.')
    parser.add_argument('--m-fac', type=float, default=1.0,
                        help='The factor to scale output colorfulness by.')
    parser.add_argument('--set-palette', action='store_true',
                        help='Set the current terminal tab\'s palette to the output color scheme.')
    args = parser.parse_args()

    scheme = plistlib.load(args.src_scheme)
    for i, row_name in enumerate(ROWS_TRANSLATE):
        row = scheme[row_name]
        rgb = np.float64([row[column] for column in COLUMNS])
        invert_J = args.invert and row_name in ROWS_INVERT
        j_fac = 1 if row_name in ROWS_INVERT else args.j_fac
        rgb_dst = translate(rgb, get_conds(args.src_bg), get_conds(args.dst_bg),
                            invert_J=invert_J, J_factor=j_fac, M_factor=args.m_fac)
        for j, column in enumerate(COLUMNS):
            row[column] = rgb_dst[j]
        print('{:<18} {} → {}'.format(row_name, format_rgb(rgb), format_rgb(rgb_dst)))
        if args.set_palette:
            n = '0123456789abcdefghilm'[i]
            rgb_ = np.uint8(np.round(rgb_dst * 255))
            esc = '\033]P{:s}{:02x}{:02x}{:02x}\033\\'.format(n, *rgb_)
            print(esc, end='', flush=True)
    plistlib.dump(scheme, args.dst_scheme)

if __name__ == '__main__':
    main()
