import os
import unittest

from mutwo import core_events
from mutwo import core_parameters
from mutwo import csound_converters

FILE_PATH = "/".join(os.path.realpath(__file__).split("/")[:-1])


class ChrononWithPitchAndPathAttribute(core_events.Chronon):
    """Chronon with additional hertz and path attributes.

    Only for testing purposes.
    """

    def __init__(
        self,
        hertz: float,
        duration: core_parameters.abc.Duration.Type,
        path: str,
        **kwargs,
    ):
        super().__init__(duration, **kwargs)
        self.hertz = hertz
        self.path = path


class EventToCsoundScoreTest(unittest.TestCase):
    test_path = f"{FILE_PATH}/test.sco"

    @classmethod
    def setUpClass(cls):
        cls.converter = csound_converters.EventToCsoundScore(
            p4=lambda event: event.hertz,
            p5=lambda event: event.path,
        )

    @classmethod
    def tearDownClass(cls):
        # remove score files
        os.remove(cls.test_path)

    def test_convert_chronon(self):
        duration = 2.0
        event_to_convert = ChrononWithPitchAndPathAttribute(
            100,
            duration,
            "flute_sample.wav",
        )
        self.converter.convert(event_to_convert, self.test_path)
        expected_line = 'i 1 0.0 {} {} "{}"'.format(
            duration,
            100,
            event_to_convert.path,
        )
        with open(self.test_path, "r") as f:
            self.assertEqual(f.read(), expected_line)

    def test_convert_consecution(self):
        hertz_tuple = (300, 100, 100, 320, 720, 500)
        duration_tuple = (2, 4, 3, 6.25, 8, 1)
        paths = tuple(
            "flute_sample{}.wav".format(nth_sample)
            for nth_sample, _ in enumerate(hertz_tuple)
        )
        event_to_convert = core_events.Consecution(
            [
                ChrononWithPitchAndPathAttribute(hertz, duration, path)
                for hertz, duration, path in zip(
                    hertz_tuple, duration_tuple, paths
                )
            ]
        )
        self.converter.convert(event_to_convert, self.test_path)

        expected_line_list = [
            csound_converters.configurations.CONSECUTION_ANNOTATION
        ]

        expected_line_list.extend(
            [
                'i 1 {} {} {} "{}"'.format(
                    absolute_entry_delay.beat_count,
                    float(duration),
                    hertz,
                    path,
                )
                for absolute_entry_delay, duration, hertz, path in zip(
                    event_to_convert.absolute_time_tuple,
                    duration_tuple,
                    hertz_tuple,
                    paths,
                )
            ]
        )
        expected_line_list.extend(
            [
                ""
                for _ in range(
                    csound_converters.configurations.N_EMPTY_LINES_AFTER_COMPOUND
                )
            ]
        )
        expected_lines = "\n".join(expected_line_list)

        with open(self.test_path, "r") as f:
            self.assertEqual(f.read(), expected_lines)

    def test_convert_consecution_with_rests(self):
        path = "flute.wav"
        event_to_convert = core_events.Consecution(
            [
                ChrononWithPitchAndPathAttribute(100, 2, path),
                core_events.Chronon(2),
                ChrononWithPitchAndPathAttribute(300, 1, path),
                core_events.Chronon(3.5),
                ChrononWithPitchAndPathAttribute(200, 4, path),
            ]
        )
        self.converter.convert(event_to_convert, self.test_path)

        expected_line_list = [
            csound_converters.configurations.CONSECUTION_ANNOTATION
        ]
        expected_line_list.extend(
            [
                'i 1 {} {} {} "{}"'.format(
                    absolute_entry_delay.beat_count,
                    event.duration.beat_count,
                    event.hertz,
                    path,
                )
                for absolute_entry_delay, event in zip(
                    event_to_convert.absolute_time_tuple, event_to_convert
                )
                if hasattr(event, "hertz")
            ]
        )
        expected_line_list.extend(
            [
                ""
                for _ in range(
                    csound_converters.configurations.N_EMPTY_LINES_AFTER_COMPOUND
                )
            ]
        )
        expected_lines = "\n".join(expected_line_list)

        with open(self.test_path, "r") as f:
            self.assertEqual(f.read(), expected_lines)

    def test_convert_concurrence(self):
        hertz_tuple = (300, 100, 100, 320, 720, 500)
        duration_tuple = (2, 4, 3, 6.25, 8, 1)
        paths = tuple(
            "flute_sample{}.wav".format(nth_sample)
            for nth_sample, _ in enumerate(hertz_tuple)
        )
        event_to_convert = core_events.Concurrence(
            [
                ChrononWithPitchAndPathAttribute(hertz, duration, path)
                for hertz, duration, path in zip(
                    hertz_tuple, duration_tuple, paths
                )
            ]
        )
        self.converter.convert(event_to_convert, self.test_path)

        expected_line_list = [
            csound_converters.configurations.CONCURRENCE_ANNOTATION
        ]
        expected_line_list.extend(
            [
                'i 1 0.0 {} {} "{}"'.format(float(duration), hertz, path)
                for duration, hertz, path in zip(
                    duration_tuple, hertz_tuple, paths
                )
            ]
        )
        expected_line_list.extend(
            [
                ""
                for _ in range(
                    csound_converters.configurations.N_EMPTY_LINES_AFTER_COMPOUND
                )
            ]
        )
        expected_lines = "\n".join(expected_line_list)

        with open(self.test_path, "r") as f:
            self.assertEqual(f.read(), expected_lines)

    def test_generate_p_field_mapping(self):
        pfield_key_to_function_mapping = {
            "p1": lambda event: 100,
            "p2": None,
            "p3": lambda event: event.duration.beat_count,
            "p6": lambda event: (event.duration / 2).beat_count,
            "p5": lambda event: (event.duration * 2).beat_count,
        }
        pfields = self.converter._generate_pfield_mapping(
            pfield_key_to_function_mapping
        )
        self.assertEqual(len(pfields), len(pfield_key_to_function_mapping) + 1)

    def test_ignore_p_field_with_unsupported_type(self):
        # convert chronon with unsupported type (set) for path argument
        duration = 2.0
        event_to_convert = ChrononWithPitchAndPathAttribute(
            440,
            duration,
            # type set is unsupported
            set([1, 2, 3]),  # type: ignore
        )
        self.converter.convert(event_to_convert, self.test_path)
        expected_line = "i 1 0.0 {} {}".format(
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
            p4=lambda event: event.hertz,
            p5=lambda event: event.amplitude,
        )
        cls.converter = csound_converters.EventToSoundFile(
            cls.orchestra_path, cls.score_converter
        )

        cls.event_to_convert = core_events.Chronon(
            2,
        )
        # monkey patching
        cls.event_to_convert.hertz = 200  # type: ignore
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
