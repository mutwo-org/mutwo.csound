"""Render sound files from mutwo data via Csound.

Csound is a `"domain-specific computer programming language
for audio programming" <http://www.csounds.com/>`_.
"""

import numbers
import os
import typing
import warnings

import natsort  # type: ignore

from mutwo import core_converters
from mutwo import core_events
from mutwo import core_constants
from mutwo import core_parameters
from mutwo import csound_converters

__all__ = ("EventToCsoundScore", "EventToSoundFile")

SupportedPFieldTypes = typing.Union[core_constants.Real, str]
SupportedPFieldTypesForTypeChecker = typing.Union[numbers.Real, str]
PFieldFunction = typing.Callable[[core_events.Chronon], SupportedPFieldTypes]
PFieldDict = dict[str, typing.Optional[PFieldFunction]]


class MissingPFieldWarning(Warning):
    pass


class InvalidPFieldValueTypeWarning(Warning):
    pass


class EventToCsoundScore(core_converters.abc.EventConverter):
    """Class to convert mutwo events to a Csound score file.

    :param pfield: p-field / p-field-extraction-function pairs.

    This class helps generating score files for the `"domain-specific computer
    programming language for audio programming" Csound <http://www.csounds.com/>`_.

    :class:`EventToCsoundScore` extracts data from mutwo Events and assign it to
    specific p-fields. The mapping of Event attributes to p-field values has
    to be defined by the user via keyword arguments during class initialization.

    By default, mutwo already maps the following p-fields to the following values:

    - p1 (instrument name) to 1
    - p2 (start time) to the absolute start time of the event
    - p3 (duration) to the :attr:`duration` attribute of the event

    If p2 shall be assigned to the absolute entry delay of the event,
    it has to be set to None.

    The :class:`EventToCsoundScore` ignores any p-field that returns
    any unsupported p-field type (anything else than a string
    or a number). If the returned type is a string, :class:`EventToCsoundScore`
    automatically adds quotations marks around the string in the score file.

    All p-fields can be overwritten in the following manner:

    >>> from mutwo import csound_converters
    >>> my_converter = csound_converters.EventToCsoundScore(
    ...     p1=lambda event: 2,
    ...     p4=lambda event: event.pitch.hertz,
    ...     p5=lambda event: event.volume
    ... )

    For easier debugging of faulty score files, :mod:`mutwo` adds annotations
    when a new :class:`~mutwo.core_events.Consecution` or a new :class:`~mutwo.core_events.Concurrence`
    starts.
    """

    _default_p_field_dict: PFieldDict = {
        "p1": lambda event: 1,  # default instrument name "1"
        "p2": None,  # default to absolute start time
        "p3": lambda event: event.duration.beat_count # type: ignore
        if event.duration > 0
        else None,  # default key for duration
    }

    def __init__(self, **pfield: PFieldFunction):
        concatenated_p_field_dict: PFieldDict = dict([])
        for (
            default_p_field,
            default_p_field_function,
        ) in self._default_p_field_dict.items():
            if default_p_field not in pfield:
                concatenated_p_field_dict.update(
                    {default_p_field: default_p_field_function}
                )

        concatenated_p_field_dict.update(pfield)
        self.pfield_tuple = self._generate_pfield_mapping(concatenated_p_field_dict)

    # ###################################################################### #
    #                          static methods                                #
    # ###################################################################### #

    @staticmethod
    def _generate_pfield_mapping(
        pfield_key_to_function_mapping: PFieldDict,
    ) -> tuple[typing.Optional[PFieldFunction], ...]:
        """Maps p-fields to their respective p_field_function."""

        sorted_pfield_keys = natsort.natsorted(pfield_key_to_function_mapping.keys())
        pfield_list = []
        for key0, key1 in zip(sorted_pfield_keys, sorted_pfield_keys[1:]):
            number0, number1 = (int(pfield_name[1:]) for pfield_name in (key0, key1))
            try:
                assert number0 >= 0
            except AssertionError:
                raise ValueError(
                    f"Can't assign p-field '{key0}'. "
                    "P-field number has to bigger than 0."
                )

            pfield_list.append(pfield_key_to_function_mapping[key0])

            difference = number1 - number0
            if difference > 1:
                for _ in range(difference - 1):
                    pfield_list.append(lambda _: 0)
                warnings.warn(
                    "Couldn't find any mapping for p-fields "
                    f"between '{key0}' and '{key1}'. "
                    "Assigned these p-fields to 0.",
                    MissingPFieldWarning,
                )

        pfield_list.append(pfield_key_to_function_mapping[key1])
        return tuple(pfield_list)

    @staticmethod
    def _process_p_field_value(
        nth_p_field: int, p_field_value: typing.Any
    ) -> typing.Optional[str]:
        """Makes sure pfield value is of correct type & adds quotation marks for str."""

        if isinstance(p_field_value, SupportedPFieldTypesForTypeChecker.__args__):  # type: ignore
            # silently adding quotation marks
            if isinstance(p_field_value, str):
                p_field_value = '"{}"'.format(p_field_value)

            else:
                p_field_value = "{}".format(p_field_value)

            return p_field_value

        else:
            ignored_p_field = nth_p_field + 1
            warnings.warn(
                f"Can't assign returned value '{p_field_value}' of type "
                f"'{type(p_field_value)}' to p-field {ignored_p_field}. "
                " Supported types for p-fields include "
                f"'{repr(SupportedPFieldTypes)}'. "
                "Ignored p-field {ignored_p_field}.",
                InvalidPFieldValueTypeWarning,
            )
            return None

    # ###################################################################### #
    #           private methods (conversion of different event types)        #
    # ###################################################################### #

    def _convert_chronon(
        self,
        chronon: core_events.Chronon,
        absolute_entry_delay: core_parameters.abc.Duration,
    ) -> tuple[str, ...]:
        """Extract p-field data from chronon and write one Csound-Score line."""

        csound_score_line = "i"
        for nth_p_field, p_field_function in enumerate(self.pfield_tuple):
            # special case of absolute start time initialization
            if nth_p_field == 1 and p_field_function is None:
                csound_score_line += " {}".format(
                    absolute_entry_delay.beat_count
                )

            else:
                try:
                    p_field_value = p_field_function(chronon)  # type: ignore

                except AttributeError:
                    # if attribute couldn't be found, just make a rest
                    return tuple([])

                p_field_value = EventToCsoundScore._process_p_field_value(
                    nth_p_field, p_field_value
                )
                if p_field_value is not None:
                    csound_score_line += " {}".format(p_field_value)

        return (csound_score_line,)

    def _convert_consecution(
        self,
        consecution: core_events.Consecution,
        absolute_entry_delay: core_parameters.abc.Duration,
    ) -> tuple[str, ...]:
        csound_score_line_list = [
            csound_converters.configurations.CONSECUTION_ANNOTATION
        ]
        csound_score_line_list.extend(
            super()._convert_consecution(consecution, absolute_entry_delay)
        )

        for _ in range(
            csound_converters.configurations.N_EMPTY_LINES_AFTER_COMPOUND
        ):
            csound_score_line_list.append("")

        return tuple(csound_score_line_list)

    def _convert_concurrence(
        self,
        concurrence: core_events.Concurrence,
        absolute_entry_delay: core_parameters.abc.Duration,
    ) -> tuple[str, ...]:
        csound_score_line_list = [
            csound_converters.configurations.CONCURRENCE_ANNOTATION
        ]
        csound_score_line_list.extend(
            super()._convert_concurrence(
                concurrence, absolute_entry_delay
            )
        )
        for _ in range(
            csound_converters.configurations.N_EMPTY_LINES_AFTER_COMPOUND
        ):
            csound_score_line_list.append("")
        return tuple(csound_score_line_list)

    # ###################################################################### #
    #                             public api                                 #
    # ###################################################################### #

    def convert(self, event_to_convert: core_events.abc.Event, path: str) -> None:
        """Render csound score file (.sco) from the passed event.

        :param event_to_convert: The event that shall be rendered to a csound score
            file.
        :type event_to_convert: core_events.abc.Event
        :param path: where to write the csound score file
        :type path: str

        >>> import random
        >>> from mutwo import core_events
        >>> from mutwo import csound_converters
        >>> converter = csound_converters.EventToCsoundScore(
        ...    p4=lambda event: event.tempo_envelope.duration
        ... )
        >>> event = core_events.Consecution(
        ...    [
        ...        core_events.Chronon(
        ...             random.uniform(0.3, 1.2)
        ...        ) for _ in range(15)
        ...    ]
        ... )
        >>> for e in event:
        ...     e.tempo = core_parameters.FlexTempo(
        ...         [[0, 1], [random.uniform(10, 20), 0]]
        ...     )
        >>> converter.convert(event, 'score.sco')
        """

        csound_score_line_tuple = self._convert_event(
            event_to_convert, core_parameters.DirectDuration(0)
        )
        # convert events to strings (where each string represents one csound score line)
        # write csound score lines to file
        with open(path, "w") as f:
            f.write("\n".join(csound_score_line_tuple))


class EventToSoundFile(core_converters.abc.Converter):
    """Generate audio files with `Csound <http://www.csounds.com/>`_.

    :param csound_orchestra_path: Path to the csound orchestra (.orc) file.
    :param event_to_csound_score: The :class:`EventToCsoundScore` that shall be used
        to render the csound score file (.sco) from a mutwo event.
    :param *flag: Flag that shall be added when calling csound. Several of the supported
        csound flags can be found in :mod:`mutwo.csound_converters.constants`.
    :param remove_score_file: Set to True if :class:`EventToSoundFile` shall remove the
        csound score file after rendering. Defaults to False.

    **Disclaimer:** Before using the :class:`EventToSoundFile`, make sure
    `Csound <http://www.csounds.com/>`_ has been correctly installed on
    your system.
    """

    def __init__(
        self,
        csound_orchestra_path: str,
        event_to_csound_score: EventToCsoundScore,
        *flag: str,
        remove_score_file: bool = False,
    ):
        self.flags = flag
        self.csound_orchestra_path = csound_orchestra_path
        self.event_to_csound_score = event_to_csound_score
        self.remove_score_file = remove_score_file

    def convert(
        self,
        event_to_convert: core_events.abc.Event,
        path: str,
        score_path: typing.Optional[str] = None,
    ) -> None:
        """Render sound file from the mutwo event.

        :param event_to_convert: The event that shall be rendered.
        :type event_to_convert: core_events.abc.Event
        :param path: where to write the sound file
        :type path: str
        :param score_path: where to write the score file
        :type score_path: typing.Optional[str]
        """

        if not score_path:
            score_path = path + ".sco"

        self.event_to_csound_score.convert(event_to_convert, score_path)
        flags = " ".join(self.flags)
        command = f"{csound_converters.configurations.CSOUND_BINARY} -o {path} {flags}"
        command += " {} {}".format(self.csound_orchestra_path, score_path)

        os.system(command)

        if self.remove_score_file:
            os.remove(score_path)
