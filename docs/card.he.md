# הכרטיס

`custom:good-days-card` מציג לוח אחד מאוחד: שבת, חגים, צומות, התאריכים המשפחתיים וכל לוח שנה אחר, עם ספירה לאחור, תאריכים עבריים ושעות הדלקת נרות. אירועים חיצוניים ומשפחתיים שחלים בשבת או ביום טוב מקבלים תג אזהרה. נוגעים בשורה כדי לראות פרטים.

אפשר לערוך הכול בעורך החזותי. הכרטיס עוקב אחרי שפת Home Assistant של המשתמש (בעברית הוא מוצג מימין לשמאל).

## YAML

בדשבורדים במצב אחסון משאב הכרטיס נרשם אוטומטית. בדשבורדים במצב YAML מוסיפים את `/good_days_static/card.js` כ-JavaScript module.

```yaml
type: custom:good-days-card
title: What's coming          # optional
calendars:                    # external calendars to merge
  - calendar.family
  - calendar.school
colors:                       # optional, per source ("holidays", "family", or a calendar)
  calendar.family: "#4caf50"
days: 30                      # look-ahead, 1-400
limit: 10                     # items, 1-100
categories: [shabbat, yom_tov, minor, fast, family]   # optional, default = integration options + family
show_hebrew_date: true
show_candle_lighting: true
show_haftarah: true           # "Haftarah: ..." line under Shabbat rows and in the next-Shabbat box
show_omer: true               # during the Omer, a line with today's count
compact: false                # one line: "Next: Shabbat · in 2 days · candles 17:52"
responsive: true              # show less when the card is narrow
narrow_limit: 3               # events listed in a narrow card
location:                     # optional: this card's own place (default: the integration's)
  latitude: 32.50
  longitude: 34.89
candle_lighting: 30           # optional: minutes before sunset (default: the integration's)
havdalah: 0                   # optional: minutes after sunset, 0 = three stars
diaspora: false               # optional: two-day Yom Tov (default: the integration's)
entry_id: <optional, for a second Good Days instance>
```

## פריסה רספונסיבית

הכרטיס מתאים את עצמו לרוחב שלו עצמו ולא לרוחב המסך, ולכן כרטיס בעמודה צרה או בתא קטן בתצוגת sections מציג פחות:

| רוחב | מה רואים |
|---|---|
| **רחב**, 400 פיקסלים ומעלה | הכול. |
| **בינוני**, 280 עד 399 פיקסלים | בלי סמלי קטגוריה ובלי שורת הפטרה מתחת לשורות הרשימה; השבת או היום טוב הבא לא חוזרים מתחת לתיבת הסיכום שלהם. |
| **צר**, מתחת ל-280 פיקסלים | גם בלי תאריכים עבריים, בלי הפטרה בתיבת הסיכום ובלי הערות משניות. הספירה לאחור עוברת לשורת השעה, והרשימה נעצרת ב-`narrow_limit` אירועים. |

נגיעה בשורה עדיין מראה הכול. כדי להציג תמיד את הכרטיס המלא מגדירים `responsive: false`. בתצוגת sections אפשר לכווץ את הכרטיס עד 3 עמודות.

## מיקום ושעות משלו { #own-location-and-times }

מפעילים בעורך את **Own location and times for this card** כדי להציג בכרטיס אחד מקום אחר (העיר של ההורים, בית נופש) או מנהג מקומי (למשל ירושלים 40 דקות, חיפה 30). בוחרים את המקום במפה, ואפשר לקבוע גם הדלקת נרות, הבדלה ויום טוב אחד או שניים. כל מה שנשאר ריק עוקב אחרי האינטגרציה.

רק הכרטיס הזה משתנה: החיישנים, הטיימרים, התזכורות ו-Assist ממשיכים להשתמש בהגדרות האינטגרציה. השעות מוצגות באזור הזמן של Home Assistant, ולכן כדאי לבחור מקומות באותו אזור זמן, או להשתמש במופע שני של ימים טובים שם (ואז לקבוע `entry_id`).

## צומות, עומר והפטרה

- צום שמתקיים ברגע זה סופר לאחור עד סופו ("ends in 1:12"), ושורות צום מראות מתי הוא מתחיל ומתי הוא מסתיים.
- בעומר מופיעה שורה עם הספירה של היום (`show_omer`).
- כל שבת מציגה את ההפטרה שלה, למשל "הפטרה: ישעיהו נד:א–נה:ה" (`show_haftarah`). כששבת חלה יחד עם יום טוב, התווית היא "הפטרת שבת".

!!! info "בלי האינטגרציה"
    הכרטיס עדיין מציג את לוחות השנה שנבחרו (בלי חגים) ומראה הערה.
