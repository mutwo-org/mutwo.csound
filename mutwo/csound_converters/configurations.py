"""Configure the behaviour of :mod:`mutwo.csound_converters`."""

CSOUND_BINARY = "csound"
"""Path to csound binary."""

SEQUENTIAL_EVENT_ANNOTATION = ";; NEW SEQUENTIAL EVENT\n;;"
"""Annotation in Csound Score files when a new :class:`SequentialEvent` starts."""

SIMULTANEOUS_EVENT_ANNOTATION = ";; NEW SIMULTANEOUS EVENT\n;;"
"""Annotation in Csound Score files when a new :class:`SimultaneousEvent` starts."""

N_EMPTY_LINES_AFTER_COMPLEX_EVENT = 1
"""How many empty lines shall be written to a Csound Score file after a :class:`ComplexEvent`."""
