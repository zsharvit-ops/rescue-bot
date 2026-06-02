"""
Gemini-based field extractor.
Sends the transcript to Google Gemini and asks it to extract structured search & rescue fields.
"""

import os
import json
import google.genai as genai

_client = genai.Client(api_key=os.environ.get("GEMINI_API_KEY"))

# Ordered list of fields to extract (Hebrew label, English key)
FIELDS = [
    ("תיאור המקרה", "case_description"),
    ("שם פרטי", "first_name"),
    ("שם משפחה", "last_name"),
    ("מספר נייד", "phone"),
    ("תעודת זהות", "id_number"),
    ("גיל / תאריך לידה", "age_dob"),
    ("כתובת מגורים", "address"),
    ("הנקודה האחרונה הידועה", "last_known_location"),
    ("תיאור הנקודה האחרונה", "last_known_location_description"),
    ("כמה זמן עבר מאז הנקודה האחרונה", "time_since_last_known"),
    ("האם טייל בעבר במקום", "been_there_before"),
    ("כמה אנשים באירוע", "num_people"),
    ("שמות וגילאים של כולם", "people_names_ages"),
    ("מאיפה יצא", "departure_point"),
    ("לאן רצה להגיע", "destination"),
    ("כמה זמן בשטח", "time_in_field"),
    ("מצב רפואי וכללי כרגע", "medical_condition"),
    ("מסוגל ללכת", "can_walk"),
    ("בריא/חולה/מחלות/תרופות", "health_notes"),
    ("טלפון להודעה למשפחה", "family_contact_phone"),
    ("ביגוד מפורט", "clothing_detailed"),
    ("לבוש נוסף (בגד ים/מעיל/כובע)", "extra_clothing"),
    ("תיאור אישי", "physical_description"),
    ("משקל", "weight"),
    ("גובה", "height"),
    ("סימנים מיוחדים (פירסינג/קעקוע/צלקות/תכשיטים)", "special_marks"),
    ("נעליים (סוג/מידה/צבע/סוליה)", "shoes"),
    ("שיער, זקן, משקפיים", "hair_beard_glasses"),
    ("ארנק / כסף / כרטיסי אשראי", "wallet_money_cards"),
    ("תרמיל / תיק", "backpack_bag"),
    ("סוג טלפון / מפה / GPS", "phone_map_gps"),
    ("פנס / אמצעי תאורה", "torch_lighting"),
    ("מעשן / מצית / גפרורים", "smoking_fire"),
    ("מצלמה / פלאש", "camera_flash"),
    ("שק שינה / אוהל", "sleeping_bag_tent"),
    ("מים (כלי וכמות)", "water"),
    ("מזון", "food"),
    ("נשק", "weapon"),
    ("חבלים / ציוד טיפוס", "ropes_climbing"),
    ("סמים / אלכוהול", "drugs_alcohol"),
    ("שמיעה / מקל הליכה / הליכון", "hearing_walking_aid"),
    ("עצמאי / יכולת הישרדות / תלותי / משמעת עצמית", "independence_survival"),
    ("תחביבים / הרגלים", "hobbies_habits"),
    ("סוג רכב / צבע / סימנים מיוחדים", "vehicle"),
    ("סכסוכים משפחתיים / חברתיים", "conflicts"),
    ("שפות", "languages"),
    ("מחשב / רשתות חברתיות", "social_media"),
    ("תמונה של המחולץ", "photo_available"),
    ("שליחת מיקום (GPS)", "location_sent"),
    ("SMS Locator (CalTopo)", "caltopo_sent"),
    ("נתק בקבוצה – היכן היו פעם אחרונה יחד", "group_separation_last_together"),
    ("נתק בקבוצה – למה התפצלו", "group_separation_reason"),
    ("נתק בקבוצה – מצב האחרים בנתק", "group_separation_others_condition"),
]

FIELD_LIST_STR = "\n".join(
    f'  "{key}": "<ערך שחולץ מהתמלול, או null אם לא קיים>"'
    for _, key in FIELDS
)

SYSTEM_PROMPT = f"""
אתה מערכת לחילוץ מידע מתשאולי חילוץ והצלה.
קרא את התמלול ומלא את כל השדות הבאים ב-JSON תקין.
אם שדה לא מוזכר בתמלול — החזר null עבורו.
החזר JSON בלבד, ללא הסברים נוספים.

{{
{FIELD_LIST_STR}
}}
"""


def extract_fields(transcript: str) -> dict:
    """Extract structured fields from a Hebrew search & rescue transcript."""
    prompt = f"{SYSTEM_PROMPT}\n\nתמלול:\n{transcript}"
    response = _client.models.generate_content(
        model="gemini-1.5-flash",
        contents=prompt,
        config=genai.types.GenerateContentConfig(
            temperature=0,
            response_mime_type="application/json",
        ),
    )
    raw = response.text
    # strip markdown code fences if present
    raw = raw.strip().removeprefix("```json").removeprefix("```").removesuffix("```").strip()
    data = json.loads(raw)
    return data
