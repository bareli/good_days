# התקנה

## דרך HACS

1. פותחים את **HACS** ומחפשים **Good Days**.
2. נכנסים לאינטגרציה ובוחרים **Download**.
3. מפעילים מחדש את Home Assistant.

!!! tip "לא מוצאים בחיפוש של HACS?"
    מוסיפים אותה כמאגר מותאם אישית: ב-HACS פותחים את התפריט (שלוש נקודות), בוחרים **Custom repositories**, מזינים `https://github.com/bareli/good_days`, בוחרים בקטגוריה **Integration**, ואז מתקינים את **Good Days**.

## התקנה ידנית

מעתיקים את התיקייה `custom_components/good_days` מה[מאגר](https://github.com/bareli/good_days) אל `<config>/custom_components/` ומפעילים מחדש את Home Assistant.

## הוספת האינטגרציה

עוברים אל **Settings → Devices & services → Add integration → Good Days**.

אם האינטגרציה המובנית **Jewish Calendar** כבר מוגדרת, המיקום, ההגדרה של חו"ל ודקות הדלקת הנרות וההבדלה שלה מוצעים כברירת מחדל. הערכים מועתקים פעם אחת ואין קישור מתמשך ביניהם.

בסיום ההגדרה מופיעה בסרגל הצד הכניסה **ימים טובים** (תאריכים משפחתיים וטיימרים לשבת), והכרטיס `custom:good-days-card` זמין לדשבורדים שלכם.

## דשבורדים במצב YAML

בדשבורדים במצב אחסון (storage) משאב הכרטיס נרשם אוטומטית. בדשבורדים במצב YAML מוסיפים את `/good_days_static/card.js` כמשאב מסוג JavaScript module. פרטים ב[הכרטיס](card.md).

## אופציונלי: Assist ובלופרינטים

- למשפטי Assist צריך להעתיק שני קבצים, ראו [Assist](entities.md#assist).
- בלופרינטים מייבאים בלחיצה אחת, ראו [בלופרינטים](entities.md#blueprints).
