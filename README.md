# 🚑 בוט WhatsApp לתחקיר חילוץ והצלה

בוט Python שמקבל תמלול שיחת תשאול של צוות חילוץ דרך WhatsApp,  
מחלץ את הפרטים הרלוונטיים בעזרת GPT-4o,  
ומחזיר קובץ `.docx` מסודר עם:

- **חלק א׳** — טבלת פרטים מלאה
- **חלק ב׳** — תמלול השיחה המקורי

---

## 🛠️ דרישות

- Python 3.10+
- חשבון [Twilio](https://www.twilio.com/) עם WhatsApp Sandbox מופעל
- מפתח API של [OpenAI](https://platform.openai.com/)
- [ngrok](https://ngrok.com/) (לפיתוח מקומי)

---

## ⚡ התקנה

```bash
cd rescue-bot
pip install -r requirements.txt
cp .env.example .env
# ערוך את .env עם הפרטים שלך
```

---

## 🚀 הפעלה

### שרת WhatsApp
```bash
# טרמינל 1 — הפעל את השרת
python app.py

# טרמינל 2 — חשוף אותו לאינטרנט עם ngrok
ngrok http 5000
```

העתק את ה-URL שמתקבל מ-ngrok (לדוגמה: `https://abc123.ngrok.io`)  
ועדכן אותו בקובץ `.env` כ-`PUBLIC_URL`.

לאחר מכן הגדר ב-Twilio Console:  
**Sandbox → When a message comes in → Webhook URL:**  
```
https://abc123.ngrok.io/webhook
```

### בדיקה מקומית (ללא WhatsApp)
```bash
python test_local.py                  # הדבק תמלול ידנית
python test_local.py transcript.txt   # קרא מקובץ טקסט
```

---

## 💬 שימוש ב-WhatsApp

1. שלח הודעה לבוט:
   ```
   תמלול: [כאן כל טקסט התמלול]
   ```
2. ניתן לשלוח בהודעות מרובות ולסיים עם:
   ```
   סיום
   ```
3. הבוט יחזיר קובץ `.docx` עם הדוח המלא.

---

## 📋 שדות בטבלה

| שדה | תיאור |
|-----|--------|
| תיאור המקרה | סיכום קצר |
| שם פרטי / משפחה | |
| מספר נייד | |
| תעודת זהות | |
| הנקודה האחרונה הידועה | |
| מצב רפואי | |
| ביגוד מלא | |
| תיאור אישי | גובה, משקל, סימנים |
| ציוד | תרמיל, מים, מזון, נשק |
| רכב | סוג, צבע, סימנים |
| ועוד 40+ שדות | |

---

## 📁 מבנה הפרויקט

```
rescue-bot/
├── app.py            # שרת Flask + Twilio webhook
├── extractor.py      # חילוץ שדות עם GPT-4o
├── doc_generator.py  # יצירת קובץ Word
├── test_local.py     # בדיקה מקומית ללא WhatsApp
├── requirements.txt
└── .env.example
```
