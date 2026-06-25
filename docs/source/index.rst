.. StarhueDocs documentation master file, created by
   sphinx-quickstart on Wed Jun 24 11:13:11 2026.
   You can adapt this file completely to your liking, but it should at least
   contain the root `toctree` directive.

Starhue - Documentation
=========================

``starhue`` takes a temperature in kelvin and returns the actual sRGB color a
blackbody of that temperature would show your eye — along with the physics
behind it: the Planck spectrum, the Wien peak, Stefan–Boltzmann exitance, and
the Harvard spectral class. It also runs in reverse, turning a color back into a
correlated color temperature (CCT), and renders it all as a star card in your
terminal.

It is pure standard library — no third-party dependencies, just Python 3.8+.

.. code-block:: python

   import starhue

   starhue.temperature_to_color(5772)   # '#fff1ea'  — the Sun, a warm white
   starhue.color_to_temperature('#ffd1a3')   # 3911.0  — the inverse (CCT)

   star = starhue.Star(5772)
   star.spectral_type.letter   # 'G'
   star.appearance             # 'neutral white'

See the source repository at https://github.com/devesh-aggarwal/starhue for
installation and the command-line interface. The API reference below is
generated from the package docstrings.

.. toctree::
   :maxdepth: 2
   :caption: Contents:

   starhue.rst

