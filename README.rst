iterm_schemer
=============

``iterm_schemer`` is a utility to translate the colors in `iTerm2 <https://www.iterm2.com>`__ color schemes between dark- and light-background. Using the `CIECAM02 <https://en.wikipedia.org/wiki/CIECAM02>`__ color appearance model and the `CAM02-UCS <https://4843ec7c-89cf-4d26-a36a-0e40ebc9a3a7.s3.amazonaws.com/luo2006.pdf>`__ color space, ``iterm_schemer`` predicts and corrects for the hue, saturation, and lightness shifts that occur when naively reversing the background and foreground colors. It is also capable of bulk-editing the lightness or colorfulness of all colors in a color scheme.

Usage
-----

An example::

    python3 -m iterm_schemer InputDark.itermcolors OutputLight.itermcolors --src-bg dark --dst-bg light --invert

This command line specifies to translate the colors in InputDark to what they should be on a light background. The ``--invert`` option goes on to actually invert the lightness of the background and foreground colors, making OutputLight.itermcolors a light-background color scheme.

Adjusting lightness and colorfulness only::

    python3 -m iterm_schemer Input.itermcolors Output.itermcolors --j-fac 0.9 --m-fac 0.9

``--j-fac 0.9`` scales the lightness of all colors in the color scheme to 90% of their original values. ``--m-fac 0.9`` does the same for the colorfulness (roughly, saturation) of all colors. The lightness and colorfulness can be adjusted separately without causing hue shift.
