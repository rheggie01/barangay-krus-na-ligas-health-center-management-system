from __future__ import annotations

import argparse
import math
import random
from collections import Counter
from datetime import date, datetime, time, timedelta

from sqlalchemy import delete, func, inspect, select

from app.db.session import SessionLocal
from app.models.consultation import Consultation
from app.models.disease import Disease
from app.models.disease_case import DiseaseCase
from app.models.patient import Patient
from app.models.user import User


# =========================================================
# OPTIONAL STRUCTURED SYMPTOM SUPPORT
# =========================================================

try:
    from app.models.symptom import Symptom

    STRUCTURED_SYMPTOMS_AVAILABLE = True

except ImportError:
    Symptom = None
    STRUCTURED_SYMPTOMS_AVAILABLE = False


# =========================================================
# DEVELOPMENT DATA POLICY
# =========================================================

MOCK_PATIENT_PREFIX = "MOCK-KNL-"

# Patient.record_status is an operational enum in the
# current API schema and only accepts ACTIVE / INACTIVE.
#
# Do NOT use TEST_RECORD_ONLY here. Synthetic identity is
# carried by the MOCK-KNL-* patient_code prefix and by
# consultation / disease-case development remarks.
MOCK_RECORD_STATUS = (
    "ACTIVE"
)

MOCK_NOTE = (
    "SYNTHETIC_DEVELOPMENT_DATA | "
    "TEST RECORD ONLY | "
    "NOT OFFICIAL BARANGAY HEALTH DATA"
)

RANDOM_SEED = 20260905

DEFAULT_PATIENT_COUNT = 1500

# Generate enough encounters for smoother dashboard trends,
# while keeping the database manageable for a capstone demo.
MIN_CONSULTATIONS_PER_PATIENT = 1
MAX_CONSULTATIONS_PER_PATIENT = 4

START_DATE = date(
    2021,
    1,
    1,
)

# September 5, 2026 falls inside an incomplete week.
# Do not seed future/incomplete completed-week observations.
DEFAULT_END_DATE = date(
    2026,
    8,
    30,
)


# =========================================================
# KRUS NA LIGAS STREET REFERENCE POINTS
# =========================================================
#
# These are street/zone reference coordinates already aligned
# with the project surveillance map. They are NOT intended to
# represent exact patient homes.
# =========================================================

STREETS = [
    {
        "street": "Angeles St.",
        "latitude": 14.64490,
        "longitude": 121.06270,
        "zone": "Zone 1",
    },
    {
        "street": "Baluyot St.",
        "latitude": 14.64610,
        "longitude": 121.06300,
        "zone": "Zone 1",
    },
    {
        "street": "C.P. Garcia",
        "latitude": 14.64770,
        "longitude": 121.06480,
        "zone": "Zone 2",
    },
    {
        "street": "E. Ramos St.",
        "latitude": 14.64365,
        "longitude": 121.06475,
        "zone": "Zone 3",
    },
    {
        "street": "Eugenio St.",
        "latitude": 14.64555,
        "longitude": 121.06330,
        "zone": "Zone 1",
    },
    {
        "street": "Fernando St.",
        "latitude": 14.64415,
        "longitude": 121.06465,
        "zone": "Zone 3",
    },
    {
        "street": "Flores St.",
        "latitude": 14.64360,
        "longitude": 121.06420,
        "zone": "Zone 3",
    },
    {
        "street": "Gonzales St.",
        "latitude": 14.64455,
        "longitude": 121.06535,
        "zone": "Zone 4",
    },
    {
        "street": "Kabaitan",
        "latitude": 14.64565,
        "longitude": 121.06295,
        "zone": "Zone 1",
    },
    {
        "street": "Maginhawa",
        "latitude": 14.64510,
        "longitude": 121.06610,
        "zone": "Zone 4",
    },
    {
        "street": "M. Dela Cruz St.",
        "latitude": 14.64395,
        "longitude": 121.06385,
        "zone": "Zone 3",
    },
    {
        "street": "Manansala St.",
        "latitude": 14.64475,
        "longitude": 121.06425,
        "zone": "Zone 3",
    },
    {
        "street": "P. Francisco St.",
        "latitude": 14.64465,
        "longitude": 121.06480,
        "zone": "Zone 4",
    },
    {
        "street": "Panginiban",
        "latitude": 14.64580,
        "longitude": 121.06430,
        "zone": "Zone 2",
    },
    {
        "street": "Salvador St.",
        "latitude": 14.64515,
        "longitude": 121.06320,
        "zone": "Zone 1",
    },
    {
        "street": "Santos St.",
        "latitude": 14.64495,
        "longitude": 121.06365,
        "zone": "Zone 2",
    },
    {
        "street": "T. Fulgencio St.",
        "latitude": 14.64375,
        "longitude": 121.06445,
        "zone": "Zone 3",
    },
    {
        "street": "Tiburcio St.",
        "latitude": 14.64425,
        "longitude": 121.06510,
        "zone": "Zone 4",
    },
    {
        "street": "Tiburcio Ext.",
        "latitude": 14.64390,
        "longitude": 121.06550,
        "zone": "Zone 4",
    },
    {
        "street": "V. Francisco St.",
        "latitude": 14.64465,
        "longitude": 121.06290,
        "zone": "Zone 1",
    },
]


# =========================================================
# SYNTHETIC NAMES
# =========================================================

MALE_FIRST_NAMES = [
    "Adrian",
    "Aldrin",
    "Andrei",
    "Angelo",
    "Arvin",
    "Ben",
    "Carlo",
    "Christian",
    "Daniel",
    "Dennis",
    "Edgar",
    "Edward",
    "Elijah",
    "Enzo",
    "Francis",
    "Gabriel",
    "Gerald",
    "Ian",
    "Ivan",
    "James",
    "Jerome",
    "John",
    "Joshua",
    "Justin",
    "Karl",
    "Kenneth",
    "Kevin",
    "Lance",
    "Luis",
    "Mark",
    "Michael",
    "Miguel",
    "Nathan",
    "Noel",
    "Paolo",
    "Patrick",
    "Paul",
    "Rafael",
    "Ramon",
    "Renzo",
    "Richard",
    "Robert",
    "Ryan",
    "Samuel",
    "Sean",
    "Steven",
    "Tristan",
    "Vincent",
]

FEMALE_FIRST_NAMES = [
    "Angela",
    "Anna",
    "Bea",
    "Bianca",
    "Camille",
    "Carla",
    "Catherine",
    "Christine",
    "Claire",
    "Daniela",
    "Diana",
    "Elaine",
    "Ella",
    "Erica",
    "Faith",
    "Gabriela",
    "Hazel",
    "Isabel",
    "Janelle",
    "Jasmine",
    "Joanna",
    "Julia",
    "Karen",
    "Kate",
    "Katrina",
    "Kim",
    "Kristine",
    "Lara",
    "Lea",
    "Liza",
    "Mae",
    "Maria",
    "Michelle",
    "Nicole",
    "Patricia",
    "Rachel",
    "Rica",
    "Rina",
    "Rose",
    "Samantha",
    "Sarah",
    "Sophia",
    "Stephanie",
    "Theresa",
    "Trisha",
    "Vanessa",
    "Victoria",
    "Yvonne",
]

MIDDLE_NAMES = [
    "Aguilar",
    "Aquino",
    "Bautista",
    "Castillo",
    "Castro",
    "Cruz",
    "David",
    "Diaz",
    "Flores",
    "Garcia",
    "Gomez",
    "Hernandez",
    "Lopez",
    "Mendoza",
    "Navarro",
    "Reyes",
    "Rivera",
    "Santos",
    "Torres",
    "Villanueva",
]

LAST_NAMES = [
    "Abad",
    "Aguilar",
    "Aquino",
    "Bautista",
    "Castillo",
    "Castro",
    "Cruz",
    "Dela Cruz",
    "Diaz",
    "Domingo",
    "Flores",
    "Garcia",
    "Gomez",
    "Gonzales",
    "Hernandez",
    "Lim",
    "Lopez",
    "Mendoza",
    "Mercado",
    "Navarro",
    "Ocampo",
    "Pascual",
    "Ramos",
    "Reyes",
    "Rivera",
    "Salazar",
    "Santos",
    "Soriano",
    "Torres",
    "Valdez",
    "Villanueva",
]

SUFFIXES = [
    None,
    None,
    None,
    None,
    None,
    None,
    None,
    "Jr.",
    "III",
]


# =========================================================
# DISEASE DEFINITIONS
# =========================================================

DISEASE_DEFINITIONS = {
    "DENGUE": {
        "name":
            "Dengue",

        "category":
            "Communicable Disease",

        "transmission_type":
            "Vector-borne",

        "is_communicable":
            True,

        "is_reportable":
            True,

        "symptoms": [
            "FEVER",
            "HEADACHE",
            "BODY_PAIN",
            "NAUSEA",
            "RASH",
            "FATIGUE",
            "LOSS_OF_APPETITE",
        ],

        "chief_complaints": [
            "Fever with headache and body pain",
            "Persistent fever and weakness",
            "Fever with body pain and nausea",
        ],
    },

    "ARI": {
        "name":
            "Acute Respiratory Infection (ARI)",

        "category":
            "Respiratory Disease",

        "transmission_type":
            "Respiratory",

        "is_communicable":
            True,

        "is_reportable":
            False,

        "symptoms": [
            "COUGH",
            "RUNNY_NOSE",
            "SORE_THROAT",
            "FEVER",
            "DIFFICULTY_BREATHING",
            "FATIGUE",
        ],

        "chief_complaints": [
            "Cough and colds",
            "Cough with sore throat",
            "Respiratory symptoms with fever",
        ],
    },

    "ILI": {
        "name":
            "Influenza-Like Illness (ILI)",

        "category":
            "Respiratory Disease",

        "transmission_type":
            "Respiratory",

        "is_communicable":
            True,

        "is_reportable":
            True,

        "symptoms": [
            "FEVER",
            "COUGH",
            "SORE_THROAT",
            "BODY_PAIN",
            "FATIGUE",
            "CHILLS",
            "HEADACHE",
        ],

        "chief_complaints": [
            "Fever with cough and body pain",
            "Flu-like symptoms",
            "Fever, chills, and cough",
        ],
    },

    "DIARRHEA_GASTROENTERITIS": {
        "name":
            "Diarrhea / Gastroenteritis",

        "category":
            "Gastrointestinal Disease",

        "transmission_type":
            "Food/Water-related",

        "is_communicable":
            True,

        "is_reportable":
            False,

        "symptoms": [
            "DIARRHEA",
            "ABDOMINAL_PAIN",
            "VOMITING",
            "NAUSEA",
            "FEVER",
            "LOSS_OF_APPETITE",
            "FATIGUE",
        ],

        "chief_complaints": [
            "Loose bowel movement and abdominal pain",
            "Diarrhea with nausea",
            "Abdominal pain with vomiting",
        ],
    },
}


# =========================================================
# STREET HOTSPOT WEIGHTS
# =========================================================
#
# Development-only artificial spatial pattern.
# This is not an epidemiological claim about Krus na Ligas.
# =========================================================

HOTSPOT_STREETS = {
    "DENGUE": {
        "Manansala St.",
        "P. Francisco St.",
        "Fernando St.",
        "M. Dela Cruz St.",
        "Tiburcio St.",
    },

    "ARI": {
        "Angeles St.",
        "Santos St.",
        "Salvador St.",
        "V. Francisco St.",
        "Eugenio St.",
    },

    "ILI": {
        "Santos St.",
        "Salvador St.",
        "Angeles St.",
        "Baluyot St.",
        "Panginiban",
    },

    "DIARRHEA_GASTROENTERITIS": {
        "M. Dela Cruz St.",
        "Flores St.",
        "Gonzales St.",
        "Fernando St.",
        "T. Fulgencio St.",
    },
}


# =========================================================
# DATE / DEMOGRAPHIC HELPERS
# =========================================================

def _random_date_between(
    rng: random.Random,
    start_date: date,
    end_date: date,
) -> date:
    day_range = (
        end_date
        - start_date
    ).days

    return (
        start_date
        + timedelta(
            days=rng.randint(
                0,
                day_range,
            )
        )
    )


def _age_on_date(
    birth_date: date,
    reference_date: date,
) -> int:
    return (
        reference_date.year
        - birth_date.year
        - (
            (
                reference_date.month,
                reference_date.day,
            )
            <
            (
                birth_date.month,
                birth_date.day,
            )
        )
    )


def _generate_birth_date(
    rng: random.Random,
) -> date:
    # Development demographic mix.
    age_group = rng.choices(
        population=[
            "0_9",
            "10_19",
            "20_39",
            "40_59",
            "60_84",
        ],
        weights=[
            18,
            17,
            32,
            21,
            12,
        ],
        k=1,
    )[0]

    ranges = {
        "0_9":
            (0, 9),

        "10_19":
            (10, 19),

        "20_39":
            (20, 39),

        "40_59":
            (40, 59),

        "60_84":
            (60, 84),
    }

    minimum_age, maximum_age = (
        ranges[
            age_group
        ]
    )

    age = rng.randint(
        minimum_age,
        maximum_age,
    )

    reference = date(
        2026,
        9,
        5,
    )

    year = (
        reference.year
        - age
    )

    month = rng.randint(
        1,
        12,
    )

    # Keep day safe for all months.
    day = rng.randint(
        1,
        28,
    )

    birth_date = date(
        year,
        month,
        day,
    )

    if birth_date > reference:
        birth_date = birth_date.replace(
            year=year - 1
        )

    return birth_date


def _civil_status_for_age(
    rng: random.Random,
    age: int,
) -> str:
    if age < 18:
        return "Single"

    if age < 25:
        return rng.choices(
            [
                "Single",
                "Married",
            ],
            weights=[
                88,
                12,
            ],
            k=1,
        )[0]

    if age < 50:
        return rng.choices(
            [
                "Single",
                "Married",
                "Separated",
            ],
            weights=[
                36,
                58,
                6,
            ],
            k=1,
        )[0]

    return rng.choices(
        [
            "Single",
            "Married",
            "Widowed",
            "Separated",
        ],
        weights=[
            18,
            60,
            17,
            5,
        ],
        k=1,
    )[0]


# =========================================================
# ARTIFICIAL TEMPORAL PATTERN
# =========================================================

def _month_weight(
    disease_code: str,
    month: int,
) -> float:
    if disease_code == "DENGUE":
        return {
            1: 0.45,
            2: 0.42,
            3: 0.45,
            4: 0.55,
            5: 0.75,
            6: 1.15,
            7: 1.55,
            8: 1.85,
            9: 1.90,
            10: 1.65,
            11: 1.15,
            12: 0.70,
        }[month]

    if disease_code == "ARI":
        return {
            1: 1.35,
            2: 1.20,
            3: 1.00,
            4: 0.85,
            5: 0.80,
            6: 0.90,
            7: 1.00,
            8: 1.05,
            9: 1.00,
            10: 1.05,
            11: 1.20,
            12: 1.40,
        }[month]

    if disease_code == "ILI":
        return {
            1: 1.20,
            2: 1.05,
            3: 0.85,
            4: 0.75,
            5: 0.80,
            6: 1.10,
            7: 1.30,
            8: 1.35,
            9: 1.20,
            10: 1.05,
            11: 1.10,
            12: 1.30,
        }[month]

    return {
        1: 0.90,
        2: 0.90,
        3: 1.05,
        4: 1.25,
        5: 1.35,
        6: 1.10,
        7: 0.95,
        8: 0.95,
        9: 1.00,
        10: 1.00,
        11: 0.95,
        12: 0.90,
    }[month]


def _generate_weighted_case_date(
    rng: random.Random,
    disease_code: str,
    start_date: date,
    end_date: date,
) -> date:
    for _ in range(
        100
    ):
        candidate = (
            _random_date_between(
                rng,
                start_date,
                end_date,
            )
        )

        probability = min(
            1.0,
            (
                _month_weight(
                    disease_code,
                    candidate.month,
                )
                / 1.90
            ),
        )

        if (
            rng.random()
            <= probability
        ):
            return candidate

    return _random_date_between(
        rng,
        start_date,
        end_date,
    )


# =========================================================
# DISEASE / STREET ASSIGNMENT
# =========================================================

def _select_disease_code(
    rng: random.Random,
) -> str:
    return rng.choices(
        population=[
            "ARI",
            "ILI",
            "DENGUE",
            "DIARRHEA_GASTROENTERITIS",
        ],
        weights=[
            34,
            25,
            25,
            16,
        ],
        k=1,
    )[0]


def _select_street_for_disease(
    rng: random.Random,
    disease_code: str,
) -> dict:
    hotspot_names = (
        HOTSPOT_STREETS[
            disease_code
        ]
    )

    weights = [
        (
            2.5
            if street[
                "street"
            ] in hotspot_names
            else 1.0
        )
        for street in STREETS
    ]

    return rng.choices(
        population=STREETS,
        weights=weights,
        k=1,
    )[0]


# =========================================================
# VITALS / SYMPTOMS
# =========================================================

def _bounded_gauss(
    rng: random.Random,
    mean: float,
    stddev: float,
    minimum: float,
    maximum: float,
    digits: int = 1,
):
    value = rng.gauss(
        mean,
        stddev,
    )

    value = min(
        maximum,
        max(
            minimum,
            value,
        ),
    )

    return round(
        value,
        digits,
    )


def _generate_vitals(
    rng: random.Random,
    disease_code: str,
    age: int,
):
    if disease_code == "DENGUE":
        temperature = _bounded_gauss(
            rng,
            38.5,
            0.65,
            36.8,
            40.2,
        )

        heart_rate = int(
            _bounded_gauss(
                rng,
                97,
                13,
                65,
                132,
                0,
            )
        )

        respiratory_rate = int(
            _bounded_gauss(
                rng,
                20,
                3,
                14,
                30,
                0,
            )
        )

        spo2 = _bounded_gauss(
            rng,
            97.5,
            1.0,
            94,
            100,
        )

    elif disease_code == "ARI":
        temperature = _bounded_gauss(
            rng,
            37.8,
            0.65,
            36.4,
            39.8,
        )

        heart_rate = int(
            _bounded_gauss(
                rng,
                91,
                12,
                60,
                128,
                0,
            )
        )

        respiratory_rate = int(
            _bounded_gauss(
                rng,
                21,
                4,
                14,
                34,
                0,
            )
        )

        spo2 = _bounded_gauss(
            rng,
            96.8,
            1.6,
            91,
            100,
        )

    elif disease_code == "ILI":
        temperature = _bounded_gauss(
            rng,
            38.1,
            0.6,
            36.7,
            40.0,
        )

        heart_rate = int(
            _bounded_gauss(
                rng,
                94,
                12,
                62,
                130,
                0,
            )
        )

        respiratory_rate = int(
            _bounded_gauss(
                rng,
                20,
                3,
                14,
                32,
                0,
            )
        )

        spo2 = _bounded_gauss(
            rng,
            97.2,
            1.2,
            93,
            100,
        )

    else:
        temperature = _bounded_gauss(
            rng,
            37.5,
            0.55,
            36.3,
            39.3,
        )

        heart_rate = int(
            _bounded_gauss(
                rng,
                88,
                11,
                58,
                122,
                0,
            )
        )

        respiratory_rate = int(
            _bounded_gauss(
                rng,
                19,
                2.5,
                14,
                29,
                0,
            )
        )

        spo2 = _bounded_gauss(
            rng,
            98.0,
            0.8,
            95,
            100,
        )

    # Development-only generalized BP / anthropometrics.
    if age < 12:
        systolic = rng.randint(
            88,
            112,
        )

        diastolic = rng.randint(
            55,
            75,
        )

        weight = _bounded_gauss(
            rng,
            28,
            10,
            7,
            55,
        )

        height = _bounded_gauss(
            rng,
            125,
            22,
            65,
            165,
        )

    elif age < 18:
        systolic = rng.randint(
            95,
            125,
        )

        diastolic = rng.randint(
            60,
            82,
        )

        weight = _bounded_gauss(
            rng,
            52,
            12,
            25,
            90,
        )

        height = _bounded_gauss(
            rng,
            158,
            11,
            125,
            185,
        )

    else:
        systolic = int(
            _bounded_gauss(
                rng,
                119,
                15,
                90,
                170,
                0,
            )
        )

        diastolic = int(
            _bounded_gauss(
                rng,
                77,
                10,
                55,
                110,
                0,
            )
        )

        weight = _bounded_gauss(
            rng,
            62,
            14,
            35,
            115,
        )

        height = _bounded_gauss(
            rng,
            162,
            9,
            140,
            190,
        )

    return {
        "temperature":
            temperature,

        "systolic_bp":
            systolic,

        "diastolic_bp":
            diastolic,

        "heart_rate":
            heart_rate,

        "respiratory_rate":
            respiratory_rate,

        "oxygen_saturation":
            spo2,

        "weight_kg":
            weight,

        "height_cm":
            height,
    }


def _select_symptom_codes(
    rng: random.Random,
    disease_code: str,
) -> list[str]:
    options = (
        DISEASE_DEFINITIONS[
            disease_code
        ][
            "symptoms"
        ]
    )

    minimum = 3
    maximum = min(
        6,
        len(
            options
        ),
    )

    count = rng.randint(
        minimum,
        maximum,
    )

    selected = rng.sample(
        options,
        k=count,
    )

    # Keep fever/cough/diarrhea anchors where appropriate.
    required = {
        "DENGUE":
            "FEVER",

        "ARI":
            "COUGH",

        "ILI":
            "FEVER",

        "DIARRHEA_GASTROENTERITIS":
            "DIARRHEA",
    }[
        disease_code
    ]

    if required not in selected:
        selected[
            0
        ] = required

    return list(
        dict.fromkeys(
            selected
        )
    )


# =========================================================
# DISEASE MASTER
# =========================================================

def _ensure_diseases(
    db,
):
    """
    Reuse the existing Disease master whenever possible.

    The project database may already contain a row such as:

        name = "Dengue"

    but with a legacy / different code.

    Because Disease.name is unique, checking only by the new
    development code can incorrectly attempt to insert another
    "Dengue" row and trigger MySQL error 1062.

    Matching order:
    1. exact disease code
    2. exact canonical disease name, case-insensitive/trimmed
    3. create only when neither exists

    Existing disease codes/names are NOT rewritten by this seed.
    """
    disease_map = {}

    for (
        code,
        definition,
    ) in DISEASE_DEFINITIONS.items():
        canonical_name = (
            definition[
                "name"
            ].strip()
        )

        disease_by_code = db.scalar(
            select(
                Disease
            ).where(
                Disease.code
                == code
            )
        )

        disease_by_name = db.scalar(
            select(
                Disease
            ).where(
                func.lower(
                    func.trim(
                        Disease.name
                    )
                )
                == canonical_name.lower()
            )
        )

        # A conflicting code row and name row would make the
        # development mapping ambiguous. Do not guess.
        if (
            disease_by_code
            is not None
            and disease_by_name
            is not None
            and disease_by_code.id
            != disease_by_name.id
        ):
            raise RuntimeError(
                "Ambiguous disease master mapping for "
                f"{code} / {canonical_name}. "
                f"Code matched disease id={disease_by_code.id} "
                f"({disease_by_code.name!r}) while name matched "
                f"disease id={disease_by_name.id} "
                f"(code={disease_by_name.code!r}). "
                "Resolve the duplicate/conflicting disease master "
                "records before seeding."
            )

        disease = (
            disease_by_code
            or disease_by_name
        )

        if disease is not None:
            match_method = (
                "code"
                if disease_by_code
                is not None
                else "name"
            )

            print(
                "[REUSE] "
                f"{code} -> existing disease "
                f"id={disease.id}, "
                f"code={disease.code!r}, "
                f"name={disease.name!r} "
                f"(matched by {match_method})"
            )

            disease_map[
                code
            ] = disease

            continue

        disease = Disease(
            code=code,

            name=canonical_name,

            category=definition[
                "category"
            ],

            transmission_type=(
                definition[
                    "transmission_type"
                ]
            ),

            description=(
                "Development disease master "
                "entry for synthetic "
                "surveillance testing."
            ),

            is_communicable=(
                definition[
                    "is_communicable"
                ]
            ),

            is_reportable=(
                definition[
                    "is_reportable"
                ]
            ),

            is_sensitive=False,

            privacy_category=(
                "STANDARD"
            ),

            is_active=True,
        )

        db.add(
            disease
        )

        db.flush()

        print(
            "[CREATED] "
            f"{code} -> disease "
            f"id={disease.id}, "
            f"name={disease.name!r}"
        )

        disease_map[
            code
        ] = disease

    return disease_map


# =========================================================
# USERS
# =========================================================

def _find_active_user_by_role(
    db,
    role_name: str,
):
    users = db.scalars(
        select(
            User
        ).where(
            User.is_active.is_(
                True
            )
        )
    ).all()

    for user in users:
        role_names = {
            role.name
            for role in user.roles
        }

        if role_name in role_names:
            return user

    return None


def _resolve_users(
    db,
):
    validator = (
        _find_active_user_by_role(
            db,
            "DOCTOR",
        )
    )

    recorder = (
        _find_active_user_by_role(
            db,
            "NURSE",
        )
        or
        _find_active_user_by_role(
            db,
            "MIDWIFE",
        )
        or
        _find_active_user_by_role(
            db,
            "BHW",
        )
        or validator
    )

    if validator is None:
        validator = db.scalar(
            select(
                User
            ).where(
                User.is_active.is_(
                    True
                )
            )
            .order_by(
                User.id.asc()
            )
        )

        print(
            "[WARNING] No active DOCTOR user found. "
            "Synthetic VALIDATED cases will use the first "
            "active user as validator for development only."
        )

    if recorder is None:
        recorder = validator

    if validator is None:
        raise RuntimeError(
            "No active user exists. Create at least one "
            "active account before seeding mock surveillance."
        )

    return (
        recorder,
        validator,
    )


# =========================================================
# STRUCTURED SYMPTOM LOOKUP
# =========================================================

def _load_symptom_map(
    db,
):
    if not STRUCTURED_SYMPTOMS_AVAILABLE:
        print(
            "[INFO] Symptom model not available. "
            "Free-text symptoms will still be populated."
        )

        return {}

    all_required_codes = sorted(
        {
            symptom_code
            for definition
            in DISEASE_DEFINITIONS.values()
            for symptom_code
            in definition[
                "symptoms"
            ]
        }
    )

    symptoms = db.scalars(
        select(
            Symptom
        ).where(
            Symptom.code.in_(
                all_required_codes
            ),
            Symptom.is_active.is_(
                True
            ),
        )
    ).all()

    symptom_map = {
        symptom.code:
            symptom
        for symptom in symptoms
    }

    missing = [
        code
        for code
        in all_required_codes
        if code not in symptom_map
    ]

    if missing:
        print(
            "[WARNING] Structured symptom codes missing: "
            + ", ".join(
                missing
            )
        )

        print(
            "[WARNING] Missing codes will remain available "
            "as free-text symptom notes only."
        )

    return symptom_map


# =========================================================
# CLEANUP
# =========================================================

def remove_existing_mock_data(
    db,
):
    mock_patient_ids = list(
        db.scalars(
            select(
                Patient.id
            ).where(
                Patient.patient_code.like(
                    f"{MOCK_PATIENT_PREFIX}%"
                )
            )
        ).all()
    )

    if not mock_patient_ids:
        return 0

    db.execute(
        delete(
            DiseaseCase
        ).where(
            DiseaseCase.patient_id.in_(
                mock_patient_ids
            )
        )
    )

    db.execute(
        delete(
            Consultation
        ).where(
            Consultation.patient_id.in_(
                mock_patient_ids
            )
        )
    )

    db.execute(
        delete(
            Patient
        ).where(
            Patient.id.in_(
                mock_patient_ids
            )
        )
    )

    db.flush()

    return len(
        mock_patient_ids
    )


# =========================================================
# PATIENT GENERATION
# =========================================================

def _build_patient(
    rng: random.Random,
    index: int,
    primary_street: dict,
):
    sex = rng.choice(
        [
            "Male",
            "Female",
        ]
    )

    first_name = (
        rng.choice(
            MALE_FIRST_NAMES
        )
        if sex == "Male"
        else rng.choice(
            FEMALE_FIRST_NAMES
        )
    )

    birth_date = (
        _generate_birth_date(
            rng
        )
    )

    reference_date = date(
        2026,
        9,
        5,
    )

    age = _age_on_date(
        birth_date,
        reference_date,
    )

    middle_name = rng.choice(
        MIDDLE_NAMES
    )

    last_name = rng.choice(
        LAST_NAMES
    )

    suffix = (
        rng.choice(
            SUFFIXES
        )
        if sex == "Male"
        else None
    )

    # Patient schema has no suffix column in the current
    # model, so include it only in the synthetic full name
    # context through emergency contact naming.
    display_suffix = (
        f" {suffix}"
        if suffix
        else ""
    )

    address = (
        f"{primary_street['zone']}, "
        f"{primary_street['street']}, "
        "Brgy. Krus na Ligas, "
        "Quezon City"
    )

    candidate_values = {
        "patient_code":
            (
                f"{MOCK_PATIENT_PREFIX}"
                f"{index:06d}"
            ),

        "first_name":
            first_name,

        "middle_name":
            middle_name,

        "last_name":
            last_name,

        "date_of_birth":
            birth_date,

        "sex":
            sex,

        "civil_status":
            _civil_status_for_age(
                rng,
                age,
            ),

        "street":
            primary_street[
                "street"
            ],

        "barangay":
            "Krus na Ligas",

        "city":
            "Quezon City",

        "address":
            address,

        # These are included only when the current Patient
        # model actually has the corresponding columns.
        #
        # Some project revisions store only street/address
        # and let SurveillanceMap resolve the canonical
        # street reference coordinate separately.
        "latitude":
            primary_street[
                "latitude"
            ],

        "longitude":
            primary_street[
                "longitude"
            ],

        # Clearly synthetic identifiers; these must never be
        # presented as real resident contact information.
        "contact_number":
            f"MOCK-{index:07d}",

        "emergency_contact_name":
            (
                f"Mock Contact for "
                f"{first_name} "
                f"{last_name}"
                f"{display_suffix}"
            ),

        "emergency_contact_number":
            f"MOCK-E-{index:07d}",

        "record_status":
            MOCK_RECORD_STATUS,
    }

    mapped_columns = {
        attribute.key
        for attribute
        in inspect(
            Patient
        ).column_attrs
    }

    patient_values = {
        key:
            value
        for (
            key,
            value,
        ) in candidate_values.items()
        if key in mapped_columns
    }

    skipped_fields = sorted(
        set(
            candidate_values
        )
        - mapped_columns
    )

    # Print this only for the first patient so the terminal
    # clearly reports model compatibility without 1500 repeats.
    if (
        index == 1
        and skipped_fields
    ):
        print(
            "[COMPATIBILITY] Current Patient model "
            "does not contain: "
            + ", ".join(
                skipped_fields
            )
        )

        print(
            "[COMPATIBILITY] Those optional fields "
            "will be skipped. Street/address values "
            "remain aligned with the surveillance map."
        )

    patient = Patient(
        **patient_values
    )

    return patient


# =========================================================
# CONSULTATION / CASE GENERATION
# =========================================================

def _consultation_count_for_patient(
    rng: random.Random,
) -> int:
    return rng.choices(
        population=[
            1,
            2,
            3,
            4,
        ],
        weights=[
            20,
            43,
            27,
            10,
        ],
        k=1,
    )[0]


def _generate_case_status(
    rng: random.Random,
) -> str:
    return rng.choices(
        population=[
            "CONFIRMED",
            "PROBABLE",
            "SUSPECTED",
        ],
        weights=[
            60,
            30,
            10,
        ],
        k=1,
    )[0]


def _create_consultation_and_case(
    *,
    db,
    rng: random.Random,
    patient: Patient,
    disease: Disease,
    disease_code: str,
    case_date: date,
    recorder: User,
    validator: User,
    symptom_map: dict,
):
    age = _age_on_date(
        patient.date_of_birth,
        case_date,
    )

    if age < 0:
        # Protect against historical encounter before birth.
        return False

    symptom_codes = (
        _select_symptom_codes(
            rng,
            disease_code,
        )
    )

    symptom_names = [
        (
            symptom_map[
                code
            ].name
            if code
            in symptom_map
            else code.replace(
                "_",
                " "
            ).title()
        )
        for code
        in symptom_codes
    ]

    vitals = (
        _generate_vitals(
            rng,
            disease_code,
            age,
        )
    )

    hour = rng.randint(
        8,
        16,
    )

    minute = rng.choice(
        [
            0,
            5,
            10,
            15,
            20,
            25,
            30,
            35,
            40,
            45,
            50,
            55,
        ]
    )

    consultation_datetime = (
        datetime.combine(
            case_date,
            time(
                hour=hour,
                minute=minute,
            ),
        )
    )

    chief_complaint = rng.choice(
        DISEASE_DEFINITIONS[
            disease_code
        ][
            "chief_complaints"
        ]
    )

    consultation = Consultation(
        patient_id=patient.id,

        disease_id=disease.id,

        consultation_date=(
            consultation_datetime
        ),

        chief_complaint=(
            chief_complaint
        ),

        symptoms=(
            ", ".join(
                symptom_names
            )
        ),

        temperature=(
            vitals[
                "temperature"
            ]
        ),

        systolic_bp=(
            vitals[
                "systolic_bp"
            ]
        ),

        diastolic_bp=(
            vitals[
                "diastolic_bp"
            ]
        ),

        heart_rate=(
            vitals[
                "heart_rate"
            ]
        ),

        respiratory_rate=(
            vitals[
                "respiratory_rate"
            ]
        ),

        oxygen_saturation=(
            vitals[
                "oxygen_saturation"
            ]
        ),

        weight_kg=(
            vitals[
                "weight_kg"
            ]
        ),

        height_cm=(
            vitals[
                "height_cm"
            ]
        ),

        assessment=(
            f"{MOCK_NOTE}. "
            f"Development pattern assigned to "
            f"{DISEASE_DEFINITIONS[disease_code]['name']}."
        ),

        diagnosis=(
            DISEASE_DEFINITIONS[
                disease_code
            ][
                "name"
            ]
        ),

        treatment_plan=(
            "TEST RECORD ONLY. "
            "No real clinical treatment or "
            "prescription is represented."
        ),

        notes=(
            MOCK_NOTE
        ),

        recorded_by=(
            recorder.id
        ),
    )

    # Phase 1 structured symptom compatibility.
    if hasattr(
        consultation,
        "structured_symptoms",
    ):
        consultation.structured_symptoms = [
            symptom_map[
                code
            ]
            for code
            in symptom_codes
            if code
            in symptom_map
        ]

    db.add(
        consultation
    )

    db.flush()

    onset_offset = rng.randint(
        0,
        4,
    )

    onset_date = (
        case_date
        - timedelta(
            days=onset_offset
        )
    )

    disease_case = DiseaseCase(
        patient_id=patient.id,

        consultation_id=(
            consultation.id
        ),

        disease_id=disease.id,

        case_status=(
            _generate_case_status(
                rng
            )
        ),

        onset_date=onset_date,

        case_date=case_date,

        remarks=(
            MOCK_NOTE
        ),

        validation_status=(
            "VALIDATED"
        ),

        validated_by=(
            validator.id
        ),

        validated_at=(
            consultation_datetime
            + timedelta(
                hours=2,
            )
        ),

        recorded_by=(
            recorder.id
        ),
    )

    db.add(
        disease_case
    )

    return True


# =========================================================
# MAIN SEED
# =========================================================

def seed_mock_surveillance(
    *,
    patient_count: int,
    replace: bool,
    end_date: date,
):
    rng = random.Random(
        RANDOM_SEED
    )

    db = SessionLocal()

    try:
        existing_mock_count = db.scalar(
            select(
                Patient
            ).where(
                Patient.patient_code.like(
                    f"{MOCK_PATIENT_PREFIX}%"
                )
            )
            .with_only_columns(
                Patient.id
            )
            .limit(
                1
            )
        )

        if (
            existing_mock_count
            is not None
            and not replace
        ):
            raise RuntimeError(
                "Mock surveillance records already exist. "
                "Run again with --replace to safely rebuild "
                "only MOCK-KNL-* records."
            )

        if replace:
            removed = (
                remove_existing_mock_data(
                    db
                )
            )

            print(
                f"[CLEANUP] Removed "
                f"{removed} existing "
                "MOCK-KNL-* patients."
            )

        disease_map = (
            _ensure_diseases(
                db
            )
        )

        (
            recorder,
            validator,
        ) = _resolve_users(
            db
        )

        symptom_map = (
            _load_symptom_map(
                db
            )
        )

        print(
            "============================================================"
        )

        print(
            "MOCK SURVEILLANCE DEVELOPMENT SEED"
        )

        print(
            "============================================================"
        )

        print(
            f"Patients requested: {patient_count}"
        )

        print(
            f"Date range: {START_DATE} to {end_date}"
        )

        print(
            f"Random seed: {RANDOM_SEED}"
        )

        print(
            f"Recorder: {recorder.username}"
        )

        print(
            f"Validator: {validator.username}"
        )

        print(
            "Data label: SYNTHETIC_DEVELOPMENT_DATA"
        )

        print()

        created_patients = 0
        created_consultations = 0
        created_cases = 0

        disease_counts = Counter()
        street_counts = Counter()

        for index in range(
            1,
            patient_count + 1,
        ):
            primary_disease_code = (
                _select_disease_code(
                    rng
                )
            )

            primary_street = (
                _select_street_for_disease(
                    rng,
                    primary_disease_code,
                )
            )

            patient = _build_patient(
                rng,
                index,
                primary_street,
            )

            db.add(
                patient
            )

            db.flush()

            created_patients += 1

            consultation_count = (
                _consultation_count_for_patient(
                    rng
                )
            )

            used_dates = set()

            for encounter_number in range(
                consultation_count
            ):
                disease_code = (
                    primary_disease_code
                    if encounter_number == 0
                    else _select_disease_code(
                        rng
                    )
                )

                disease = (
                    disease_map[
                        disease_code
                    ]
                )

                # Keep the patient's registered home street stable.
                # Disease spatial patterns are achieved by the initial
                # primary disease/street assignment, not by changing
                # a patient's address between encounters.
                case_date = (
                    _generate_weighted_case_date(
                        rng,
                        disease_code,
                        START_DATE,
                        end_date,
                    )
                )

                # Never create a consultation before the patient's birth.
                minimum_case_date = (
                    patient.date_of_birth
                    + timedelta(
                        days=30
                    )
                )

                if (
                    case_date
                    < minimum_case_date
                ):
                    case_date = max(
                        minimum_case_date,
                        START_DATE,
                    )

                if case_date > end_date:
                    continue

                # Avoid duplicate same-day encounters for one patient.
                retry = 0

                while (
                    case_date
                    in used_dates
                    and retry < 12
                ):
                    case_date = (
                        _generate_weighted_case_date(
                            rng,
                            disease_code,
                            START_DATE,
                            end_date,
                        )
                    )

                    retry += 1

                if case_date in used_dates:
                    continue

                used_dates.add(
                    case_date
                )

                created = (
                    _create_consultation_and_case(
                        db=db,
                        rng=rng,
                        patient=patient,
                        disease=disease,
                        disease_code=disease_code,
                        case_date=case_date,
                        recorder=recorder,
                        validator=validator,
                        symptom_map=symptom_map,
                    )
                )

                if created:
                    created_consultations += 1
                    created_cases += 1

                    disease_counts[
                        disease_code
                    ] += 1

                    street_counts[
                        patient.street
                    ] += 1

            if (
                index % 100
                == 0
            ):
                db.commit()

                print(
                    f"[PROGRESS] {index}/"
                    f"{patient_count} patients"
                )

        db.commit()

        print()

        print(
            "============================================================"
        )

        print(
            "SEED COMPLETE"
        )

        print(
            "============================================================"
        )

        print(
            f"Patients created: "
            f"{created_patients}"
        )

        print(
            f"Consultations created: "
            f"{created_consultations}"
        )

        print(
            f"Validated disease cases created: "
            f"{created_cases}"
        )

        print()

        print(
            "Disease distribution:"
        )

        for disease_code in [
            "DENGUE",
            "ARI",
            "ILI",
            "DIARRHEA_GASTROENTERITIS",
        ]:
            print(
                f"  {disease_code}: "
                f"{disease_counts[disease_code]}"
            )

        print()

        print(
            "Top street case counts:"
        )

        for (
            street,
            count,
        ) in street_counts.most_common(
            10
        ):
            print(
                f"  {street}: {count}"
            )

        print()

        print(
            "[IMPORTANT] These are synthetic "
            "development records only."
        )

        print(
            "[IMPORTANT] More synthetic records "
            "improve demo coverage/stability, "
            "not real-world clinical accuracy."
        )

    except Exception:
        db.rollback()
        raise

    finally:
        db.close()


# =========================================================
# CLI
# =========================================================

def main():
    parser = argparse.ArgumentParser(
        description=(
            "Seed synthetic Krus na Ligas "
            "surveillance development data."
        )
    )

    parser.add_argument(
        "--patients",
        type=int,
        default=DEFAULT_PATIENT_COUNT,
        help=(
            "Number of synthetic patients "
            "(default: 1500)"
        ),
    )

    parser.add_argument(
        "--replace",
        action="store_true",
        help=(
            "Delete and rebuild only existing "
            "MOCK-KNL-* synthetic records."
        ),
    )

    parser.add_argument(
        "--end-date",
        type=str,
        default=(
            DEFAULT_END_DATE.isoformat()
        ),
        help=(
            "Last allowed synthetic case date "
            "in YYYY-MM-DD format."
        ),
    )

    args = parser.parse_args()

    if args.patients < 1500:
        raise ValueError(
            "For this development seed, use at "
            "least 1500 synthetic patients."
        )

    end_date = date.fromisoformat(
        args.end_date
    )

    if end_date < START_DATE:
        raise ValueError(
            "end-date must not be earlier "
            "than START_DATE."
        )

    seed_mock_surveillance(
        patient_count=(
            args.patients
        ),
        replace=(
            args.replace
        ),
        end_date=(
            end_date
        ),
    )


if __name__ == "__main__":
    main()
