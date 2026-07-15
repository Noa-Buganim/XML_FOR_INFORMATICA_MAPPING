
# Informatica PowerCenter XML Generator - Streamlit App

## 📋 תיאור
אפליקציית Streamlit מלאה המחברת את כל ארבעת קבצי ה-Python (Delta 000, 010, 020, 030) לממשק משתמש אחד מאוחד.

## ✨ תכונות
- **4 שלבי Delta** - בחר בין DELTA 000, DELTA 010, DELTA 020, ו-DELTA 030
- **הזנת DDL דינמית** - הדבק את ה-CREATE TABLE שלך והתוכנה תחלץ את השדות
- **XML ממויד** - ייצור XML עם כל שדות הטבלה שלך
- **הורדה ישירה** - הורד את קובץ ה-XML ישירות למחשב
- **RTL עברית** - ממשק בעברית מיושר לימין

## 🚀 הרצה

### דרישות
```bash
pip install streamlit
```

### הרצת האפליקציה
```bash
streamlit run app.py
```

האפליקציה תפתח בדפדפן בכתובת `http://localhost:8501`

## 📝 שימוש

1. **בחר שלב Delta**
   - DELTA 000 - Master Key STG (ממירה CREATE TABLE לXML)
   - DELTA 010 - Master STG (עם שתי SOURCE)
   - DELTA 020 - Master CLN (Advanced Mapping)
   - DELTA 030 - Communication Detail CLN

2. **הדבק CREATE TABLE DDL**
   - הדבק את ה-CREATE TABLE הרצוי בתיבת הטקסט

3. **לחץ "ייצר קובץ XML"**
   - האפליקציה תעבד את ה-DDL ותייצר XML

4. **הורד את הקובץ**
   - לחץ על "⬇️ הורד קובץ XML" כדי להוריד את הקובץ

## 🔧 דרישות טכניות

### Python
- Python 3.8+

### ספריות
- `streamlit` - ממשק משתמש
- `xml.etree.ElementTree` - יצירת XML (מובנה)
- `xml.dom.minidom` - עיצוב XML (מובנה)
- `re` - ביטויים רגולריים (מובנה)
- `datetime` - תאריכים (מובנה)

### קובצי ייבוא
האפליקציה מכילה את כל הלוגיקה מהקבצים המקוריים:
- `PROGRAMIZ_DELTA_000_MASTER_KEY_STG.py` - פרסוםסינג DDL
- `PROGRAMIZ_DELTA_010_master_STG.py` - מיזוג דו-מקור
- `PROGRAMIZ_DELTA_020_master_cln.py` - XML מתקדם
- `PROGRAMIZ_DELTA_030_DETAIL_CLN.py` - XML לפרטים

## 📊 דוגמה CREATE TABLE

```sql
CREATE TABLE [kfk].[member_demographic](
    [TRANSACTION_ID] [bigint] IDENTITY(1,1) NOT NULL,
    [entity_id] [varchar](50) NULL,
    [action] [varchar](50) NULL,
    [entity_type] [varchar](50) NULL,
    [_data_name_family] [varchar](50) NULL,
    [_data_name_given] [varchar](50) NULL,
    [_data_timestamp_sequence] [varchar](50) NULL,
    [offset] [bigint] NULL,
    [row_create_date] [datetime] NULL
)
```

## 🎯 פלט
- **קובץ XML** עם מבנה Informatica PowerCenter מלא
- **שם קובץ** - `informatica_mapping_[DELTA].xml`
- **קידוד** - UTF-8 עם BOM עבור Windows-1255

## 🐛 פתרון בעיות

### שגיאה: "לא ניתן למצוא שם טבלה"
- וודא שה-DDL מתחיל עם `CREATE TABLE`
- בדוק שהשם בין סוגריים מרובעים

### שגיאה: "לא ניתן למצוא גוף טבלה"
- וודא שיש סוגריים `()` סביב השדות

### XML ריק או חלקי
- בדוק שהשדות מוגדרים בהתאם לתבנית
- וודא סוגי נתונים (`bigint`, `varchar`, `datetime`, וכו')

## 📞 תמיכה
לשאלות או בעיות, בדוק את:
- `PROGRAMIZ_DELTA_000_MASTER_KEY_STG.py` - ההגדרות הבסיסיות
- `PROGRAMIZ_DELTA_010_master_STG.py` - תבנית ה-SOURCE המרובה
- `PROGRAMIZ_DELTA_020_master_cln.py` - תבנית ה-XML המתקדמת
- `PROGRAMIZ_DELTA_030_DETAIL_CLN.py` - תבנית הפרטים

---
**תאריך עדכון אחרון:** 2026-07-15
**גרסה:** 1.0.0
READ ... P.md
מציג את README_APP.md.
