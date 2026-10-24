"""A short original text used for character-level training."""
TEXT = """
The workshop opens before the sun reaches the roof. A kettle clicks, the door
locks, and the first student spreads a map across the table. They are building
a small weather station from a board, a battery and three sensors. The plan is
simple: measure, record, and compare the numbers with the forecast.

By noon the sensor is outside and the screen shows a thin line of temperature.
The line rises, dips when a cloud passes, and rises again. Nobody celebrates
yet. The team wants a full week of readings before trusting the device. They
write a note on the whiteboard: check the cable, label the files, ask before
changing the code.

In the afternoon a second group arrives with a broken radio. They open the case,
test the power, and find a loose joint. The repair takes ten minutes. The radio
plays a quiet song while the weather station logs another row. Outside, the
wind moves the trees and the small screen keeps its slow, patient record.
"""

def load_data(seed=42, quick=False):
    text = TEXT.strip()[:420] if quick else TEXT.strip()
    characters = sorted(set(text))
    return {
        "text": text,
        "characters": characters,
        "vocabulary_size": len(characters),
        "sequence_length": 18 if quick else 28,
    }
