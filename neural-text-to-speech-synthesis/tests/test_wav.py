"""Tests of the WAV codec: what is written can be read back."""
import wave
from pathlib import Path

import numpy as np

from src.model import read_wav, synthesize, write_wav


def test_a_wav_file_round_trips(tmp_path):
    samples = np.array([0, 1000, -1000, 32767, -32768], dtype=np.int16)
    path = tmp_path / "out.wav"
    write_wav(path, samples, 16000)

    read_back, sample_rate = read_wav(path)
    assert sample_rate == 16000
    assert np.array_equal(read_back, samples)


def test_the_header_is_the_one_of_a_mono_file(tmp_path):
    path = tmp_path / "out.wav"
    write_wav(path, np.zeros(100, dtype=np.int16), 22050)
    with wave.open(str(path), "rb") as handle:
        assert handle.getnchannels() == 1
        assert handle.getsampwidth() == 2
        assert handle.getframerate() == 22050
        assert handle.getnframes() == 100


def test_the_parent_directory_is_created(tmp_path):
    path = tmp_path / "nested" / "deeper" / "out.wav"
    write_wav(path, np.zeros(10, dtype=np.int16))
    assert Path(path).exists()


def test_the_synthesized_audio_round_trips(tmp_path):
    samples = synthesize("hello world", 16000)
    path = tmp_path / "speech.wav"
    write_wav(path, samples, 16000)
    read_back, sample_rate = read_wav(path)
    assert sample_rate == 16000
    assert read_back.size == samples.size
    assert np.array_equal(read_back, samples)
