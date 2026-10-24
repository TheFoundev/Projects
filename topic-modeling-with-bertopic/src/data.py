"""A small news corpus with four rough themes."""
DOCUMENTS = [
    "The city approved a new bike lane along the river this week.",
    "Cyclists welcomed the riverside bike lane, while drivers asked for parking changes.",
    "Transit officials added electric buses to two busy routes on Monday.",
    "The bus fleet upgrade includes charging stations at the north depot.",
    "A local team released an open dataset of air quality readings from schools.",
    "Air quality sensors in three neighbourhoods will report hourly pollution levels.",
    "Researchers used the open air quality data to compare traffic corridors.",
    "The library extended its evening hours during the exam period.",
    "Students requested more late study space and the library added seats.",
    "The library will run a repair workshop for broken electronics next month.",
    "A community kitchen reopened after volunteers renovated the prep area.",
    "Volunteers are looking for weekend shifts at the community kitchen.",
    "The kitchen serves about two hundred meals each week.",
    "A small startup demonstrated a repair-friendly laptop with replaceable parts.",
    "The laptop uses standard screws and will sell spare batteries for five years.",
    "Reviewers noted the repair-friendly laptop is heavier than comparable models.",
]

def load_data(seed=42, quick=False):
    return {"documents": DOCUMENTS[:10] if quick else DOCUMENTS}
