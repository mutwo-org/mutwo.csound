import os
import unittest

from mutwo import core_events
from mutwo import core_constants
from mutwo import csound_converters

FILE_PATH = "/".join(os.path.realpath(__file__).split("/")[:-1])


class SimpleEventWithPitchAndPathAttribute(core_events.SimpleEvent):
    """SimpleEvent with additional frequency and path attributes.

    Only for testing purposes.
    """

    def __init__(
        self,
        frequency: float,
        duration: core_constants.DurationType,
        path: str,
    ):
        super().__init__(duration)
        self.frequency = frequency
        self.path = path


class EventToCsoundScoreTest(unittest.TestCase):
    test_path = f"{FILE_PATH}/test.sco"

    @classmethod
    def setUpClass(cls):
        cls.converter = csound_converters.EventToCsoundScore(
            p4=lambda event: event.frequency,
            p5=lambda event: event.path,
        )

    @classmethod
    def tearDownClass(cls):
        # remove score files
        os.remove(cls.test_path)

    def test_convert_simple_event(self):
        duration = 2
        event_to_convert = SimpleEventWithPitchAndPathAttribute(
            100,
            duration,
            "flute_sample.wav",
        )
        self.converter.convert(event_to_convert, self.test_path)
        expected_line = 'i 1 0 {} {} "{}"'.format(
            duration,
            100,
            event_to_convert.path,
        )
        with open(self.test_path, "r") as f:
            self.assertEqual(f.read(), expected_line)

    def test_convert_sequential_event(self):
        frequency_tuple = (300, 100, 100, 320, 720, 500)
        duration_tuple = (2, 4, 3, 6.25, 8, 1)
        paths = tuple(
            "flute_sample{}.wav".format(nth_sample)
            for nth_sample, _ in enumerate(frequency_tuple)
        )
        event_to_convert = core_events.SequentialEvent(
            [
                SimpleEventWithPitchAndPathAttribute(frequency, duration, path)
                for frequency, duration, path in zip(
                    frequency_tuple, duration_tuple, paths
                )
            ]
        )
        self.converter.convert(event_to_convert, self.test_path)

        expected_lines = [csound_converters.constants.SEQUENTIAL_EVENT_ANNOTATION]

        expected_lines.extend(
            [
                'i 1 {} {} {} "{}"'.format(
                    absolute_entry_delay, duration, frequency, path
                )
                for absolute_entry_delay, duration, frequency, path in zip(
                    event_to_convert.absolute_time_tuple,
                    duration_tuple,
                    frequency_tuple,
                    paths,
                )
            ]
        )
        expected_lines.extend(
            [
                ""
                for _ in range(
                    csound_converters.constants.N_EMPTY_LINES_AFTER_COMPLEX_EVENT
                )
            ]
        )
        expected_lines = "\n".join(expected_lines)

        with open(self.test_path, "r") as f:
            self.assertEqual(f.read(), expected_lines)

    def test_convert_sequential_event_with_rests(self):
        path = "flute.wav"
        event_to_convert = core_events.SequentialEvent(
            [
                SimpleEventWithPitchAndPathAttribute(100, 2, path),
                core_events.SimpleEvent(2),
                SimpleEventWithPitchAndPathAttribute(300, 1, path),
                core_events.SimpleEvent(3.5),
                SimpleEventWithPitchAndPathAttribute(200, 4, path),
            ]
        )
        self.converter.convert(event_to_convert, self.test_path)

        expected_lines = [csound_converters.constants.SEQUENTIAL_EVENT_ANNOTATION]
        expected_lines.extend(
            [
                'i 1 {} {} {} "{}"'.format(
                    absolute_entry_delay, event.duration, event.frequency, path
                )
                for absolute_entry_delay, event in zip(
                    event_to_convert.absolute_time_tuple, event_to_convert
                )
                if hasattr(event, "frequency")
            ]
        )
        expected_lines.extend(
            [
                ""
                for _ in range(
                    csound_converters.constants.N_EMPTY_LINES_AFTER_COMPLEX_EVENT
                )
            ]
        )
        expected_lines = "\n".join(expected_lines)

        with open(self.test_path, "r") as f:
            self.assertEqual(f.read(), expected_lines)

    def test_convert_simultaneous_event(self):
        frequency_tuple = (300, 100, 100, 320, 720, 500)
        duration_tuple = (2, 4, 3, 6.25, 8, 1)
        paths = tuple(
            "flute_sample{}.wav".format(nth_sample)
            for nth_sample, _ in enumerate(frequency_tuple)
        )
        event_to_convert = core_events.SimultaneousEvent(
            [
                SimpleEventWithPitchAndPathAttribute(frequency, duration, path)
                for frequency, duration, path in zip(
                    frequency_tuple, duration_tuple, paths
                )
            ]
        )
        self.converter.convert(event_to_convert, self.test_path)

        expected_lines = [csound_converters.constants.SIMULTANEOUS_EVENT_ANNOTATION]
        expected_lines.extend(
            [
                'i 1 0 {} {} "{}"'.format(duration, frequency, path)
                for duration, frequency, path in zip(
                    duration_tuple, frequency_tuple, paths
                )
            ]
        )
        expected_lines.extend(
            [
                ""
                for _ in range(
                    csound_converters.constants.N_EMPTY_LINES_AFTER_COMPLEX_EVENT
                )
            ]
        )
        expected_lines = "\n".join(expected_lines)

        with open(self.test_path, "r") as f:
            self.assertEqual(f.read(), expected_lines)

    def test_generate_p_field_mapping(self):
        pfield_key_to_function_mapping = {
            "p1": lambda event: 100,
            "p2": None,
            "p3": lambda event: event.duration,
            "p6": lambda event: event.duration / 2,
            "p5": lambda event: event.duration * 2,
        }
        pfields = self.converter._generate_pfield_mapping(
            pfield_key_to_function_mapping
        )
        self.assertEqual(len(pfields), len(pfield_key_to_function_mapping) + 1)

    def test_ignore_p_field_with_unsupported_type(self):
        # convert simple event with unsupported type (set) for path argument
        duration = 2
        event_to_convert = SimpleEventWithPitchAndPathAttribute(
            440,
            duration,
            # type set is unsupported
            set([1, 2, 3]),  # type: ignore
        )
        self.converter.convert(event_to_convert, self.test_path)
        expected_line = "i 1 0 {} {}".format(
            duration,
            440,
        )
        with open(self.test_path, "r") as f:
            self.assertEqual(f.read(), expected_line)


class EventToSoundFileTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        common_path = FILE_PATH
        cls.orchestra_path = "{}/test.orc".format(common_path)
        cls.score_path = "{}/test.sco".format(common_path)
        cls.soundfile_path = "{}/test.wav".format(common_path)
        with open(cls.orchestra_path, "w") as f:
            f.write(
                "sr=44100\nksmps=1\n0dbfs=1\nnchnls=1\ninstr 1\nasig poscil3 p5,"
                " p4\nout asig\nendin"
            )
        cls.score_converter = csound_converters.EventToCsoundScore(
            p4=lambda event: event.frequency,
            p5=lambda event: event.amplitude,
        )
        cls.converter = csound_converters.EventToSoundFile(
            cls.orchestra_path, cls.score_converter
        )

        cls.event_to_convert = core_events.SimpleEvent(
            2,
        )
        # monkey patching
        cls.event_to_convert.frequency = 200  # type: ignore
        cls.event_to_convert.amplitude = 0.85  # type: ignore

    @classmethod
    def tearDownClass(cls):
        # remove csound and sound files
        os.remove(cls.orchestra_path)
        os.remove(cls.score_path)
        os.remove(cls.soundfile_path)

    def test_convert(self):
        # make sure conversion method run without any errors
        # (and sound file exists)

        self.converter.convert(
            self.event_to_convert, self.soundfile_path, self.score_path
        )
        self.assertTrue(os.path.isfile(self.soundfile_path))

    def test_convert_with_remove_score_file(self):
        # make sure csound converter removes / maintains score file

        self.converter.remove_score_file = True
        self.converter.convert(
            self.event_to_convert, self.soundfile_path, self.score_path
        )
        self.assertFalse(os.path.isfile(self.score_path))

        self.converter.remove_score_file = False
        self.converter.convert(
            self.event_to_convert, self.soundfile_path, self.score_path
        )
        self.assertTrue(os.path.isfile(self.score_path))


if __name__ == "__main__":
    unittest.main()
