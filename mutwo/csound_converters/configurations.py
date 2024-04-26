"""Configure the behaviour of :mod:`mutwo.csound_converters`."""

CSOUND_BINARY = "csound"
"""Path to csound binary."""

CONSECUTION_ANNOTATION = ";; NEW CONSECUTION\n;;"
"""Annotation in Csound Score files when a new :class:`Consecution` starts."""

CONCURRENCE_ANNOTATION = ";; NEW CONCURRENCE\n;;"
"""Annotation in Csound Score files when a new :class:`Concurrence` starts."""

N_EMPTY_LINES_AFTER_COMPOUND = 1
"""How many empty lines shall be written to a Csound Score file after a :class:`Compound`."""
