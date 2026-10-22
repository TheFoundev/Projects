"""Template sentences with gazetteer entities and BIO labels."""
import numpy as np

PEOPLE = ["Mina Park", "Devon Reed", "Ari Chen", "Sam Okafor", "Priya Shah", "Jon Bell"]
ORGS = ["Northline Labs", "Cedar University", "Open Field Studio", "Harbour Transit"]
PLACES = ["Toronto", "Montreal", "Kingston", "Halifax", "Vancouver"]

TEMPLATES = [
    "{person} joined {org} in {place} last spring.",
    "{org} opened a small office in {place}, said {person}.",
    "{person} presented the {org} report at a meeting in {place}.",
    "The {place} team met {person} from {org} on Friday.",
    "{person} moved from {place} to work at {org}.",
]


def make_example(rng):
    person = str(rng.choice(PEOPLE))
    org = str(rng.choice(ORGS))
    place = str(rng.choice(PLACES))
    text = str(rng.choice(TEMPLATES)).format(person=person, org=org, place=place)
    tokens = text.replace(".", " .").split()
    labels = []
    entity_values = {value: label for value, label in [(person, "PER"), (org, "ORG"), (place, "LOC")]}

    for token in tokens:
        label = "O"
        for value, entity in entity_values.items():
            if token in value.split():
                label = entity
                break
        labels.append(label)
    return {"tokens": tokens, "labels": labels, "text": text}


def load_data(seed=42, quick=False):
    rng = np.random.default_rng(seed)
    train = [make_example(rng) for _ in range(80 if quick else 240)]
    test = [make_example(rng) for _ in range(24 if quick else 70)]
    return {"train": train, "test": test, "labels": ["PER", "ORG", "LOC"]}
