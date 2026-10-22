"""A small handbook corpus and evaluation questions."""
DOCUMENTS = [
    ("lab-hours", "The fabrication lab is open from 9:00 to 18:00 on weekdays. Weekend access requires a supervisor."),
    ("lab-booking", "Book lab equipment through the department portal at least two days in advance."),
    ("safety", "Safety glasses are required at all times in the fabrication lab. Food and drink stay outside."),
    ("printers", "The 3D printers use PLA filament. A failed print should be reported to the lab technician."),
    ("library", "The library loans laptops for four hours. Renewals are allowed if nobody is waiting."),
    ("wifi", "Campus Wi-Fi uses the eduroam network. Use your student email and password to sign in."),
    ("printing", "Students receive a printing credit of ten dollars each term. Extra pages cost five cents."),
    ("advising", "Course advising appointments open two weeks before registration. Bring a draft schedule."),
    ("health", "The health centre is in Building C. Walk-in hours are 8:30 to 11:00 on weekdays."),
    ("transit", "The campus shuttle runs every fifteen minutes between the station and the north gate."),
    ("gym", "The gym is free for students. A student card is required at the entrance."),
    ("lost", "Lost items are held at the security desk in the main lobby for fourteen days."),
]

QUESTIONS = [
    ("When does the fabrication lab open?", "The fabrication lab is open from 9:00 to 18:00 on weekdays.", "lab-hours"),
    ("How far ahead should I book lab equipment?", "Book lab equipment through the department portal at least two days in advance.", "lab-booking"),
    ("What should I wear in the fabrication lab?", "Safety glasses are required at all times in the fabrication lab.", "safety"),
    ("How long can I borrow a laptop?", "The library loans laptops for four hours.", "library"),
    ("How do I connect to campus Wi-Fi?", "Campus Wi-Fi uses the eduroam network.", "wifi"),
    ("Where is the health centre?", "The health centre is in Building C.", "health"),
    ("How often does the campus shuttle run?", "The campus shuttle runs every fifteen minutes between the station and the north gate.", "transit"),
    ("Where are lost items kept?", "Lost items are held at the security desk in the main lobby for fourteen days.", "lost"),
]


def load_data(seed=42, quick=False):
    questions = QUESTIONS[:5] if quick else QUESTIONS
    return {"documents": DOCUMENTS, "questions": questions}
