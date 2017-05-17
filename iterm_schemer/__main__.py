"""Translates iTerm2 color schemes between dark- and light-background."""

from argparse import ArgumentParser, ArgumentDefaultsHelpFormatter, FileType
import plistlib

import numpy as np

from iterm_schemer.cam02ucs import get_conds, translate

ROWS_TRANSLATE = ['Ansi %d Color' % i for i in range(16)]
ROWS_INVERT = ['Foreground', 'Background', 'Bold', 'Cursor', 'Cursor Text']
ROWS_INVERT = [k + ' Color' for k in ROWS_INVERT]
COLUMNS = ['Red Component', 'Green Component', 'Blue Component']

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
    args = parser.parse_args()

    scheme = plistlib.load(args.src_scheme)
    for row_name in ROWS_TRANSLATE + ROWS_INVERT:
        row = scheme[row_name]
        rgb = np.float64([row[column] for column in COLUMNS])
        invert_J = args.invert and row_name in ROWS_INVERT
        rgb_ = translate(rgb, get_conds(args.src_bg), get_conds(args.dst_bg),
                         invert_J=invert_J, J_factor=args.j_fac, M_factor=args.m_fac)
        for i, column in enumerate(COLUMNS):
            row[column] = rgb_[i]
        print(row_name, rgb, rgb_)
    plistlib.dump(scheme, args.dst_scheme)

if __name__ == '__main__':
    main()
