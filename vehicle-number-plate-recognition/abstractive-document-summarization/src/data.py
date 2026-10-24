"""Small built-in corpus so the project runs without a dataset download."""
import re

PAIRS = [
    ("The city opened a new protected bike lane on King Street this week. The lane connects the station to the university campus. Officials said the project took eight months and cost 1.2 million dollars. Local cycling groups welcomed the change, while some shop owners worried about loading zones. The city plans to review traffic counts after six months.",
     "The city opened a protected bike lane connecting the station to campus and will review traffic after six months."),
    ("A team of students built a low-cost air quality sensor for their capstone project. The device measures particulate matter and sends readings over Wi-Fi every five minutes. It uses a small solar panel and a rechargeable battery. The team tested it outside three schools for two weeks. Their results matched a commercial monitor within fifteen percent.",
     "Students built a solar-powered air quality sensor that sends readings every five minutes and matched a commercial monitor within fifteen percent."),
    ("The library will extend its opening hours during exams. From next Monday the main floor will stay open until midnight on weekdays. The change follows a student survey where late study space was the most requested improvement. Security staff will be added for the evening shift. The pilot will run for four weeks and may become permanent.",
     "The library is extending weekday opening hours until midnight during exams after students asked for more late study space."),
    ("Researchers released a dataset of annotated satellite images for crop monitoring. The collection covers four regions and three growing seasons. Each image includes field boundaries and crop labels checked by agronomists. The team hopes the data will help build models that work across different climates. A baseline classifier is included with the download.",
     "Researchers released a multi-region satellite image dataset with field boundaries and crop labels, plus a baseline classifier."),
    ("A small hardware startup is testing a repair-friendly laptop. The case opens with standard screws and the battery, storage and memory can be replaced without special tools. The company says spare parts will be sold for at least five years. Early reviewers praised the design but noted the laptop is heavier than comparable models. Shipping is planned for next spring.",
     "A startup is testing a repair-friendly laptop with standard screws, replaceable parts and five years of spare-part support."),
    ("The transit agency added real-time arrival displays to twelve bus stops. The displays use a low-power e-ink screen and update every thirty seconds. A solar panel keeps the unit running during the day. The agency will compare ridership and complaints at those stops with a control group. If the pilot works, forty more stops will receive displays next year.",
     "The transit agency added solar e-ink arrival displays at twelve bus stops and will compare complaints and ridership before expanding."),
    ("A community kitchen reopened after a volunteer-led renovation. The space now has a larger prep area, two new ovens and a wheelchair-accessible entrance. Donations covered most of the materials and local tradespeople donated labour. The kitchen serves about two hundred meals a week. Organizers are looking for volunteers for weekend shifts.",
     "A community kitchen reopened after a volunteer renovation with a larger prep area and accessible entrance, serving two hundred meals a week."),
    ("The university launched a peer tutoring program for first-year programming courses. Upper-year students run two drop-in sessions each week and review debugging strategies. Attendance is capped at twenty students per session. Early feedback shows that students who attended at least three sessions submitted more complete assignments. The program will continue next term.",
     "Upper-year students run weekly drop-in programming tutoring, and early feedback shows better assignment completion among regular attendees."),
]


def split_sentences(text):
    return [part.strip() for part in re.split(r"(?<=[.!?])\s+", text) if part.strip()]


def load_data(seed=42, quick=False):
    pairs = PAIRS[:4] if quick else PAIRS
    return {
        "pairs": pairs,
        "documents": [document for document, _ in pairs],
        "references": [reference for _, reference in pairs],
    }
