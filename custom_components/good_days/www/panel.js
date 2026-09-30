/* Good Days sidebar panel: family dates (birthdays, yahrzeits, anniversaries) by Hebrew date. */

const FSI = "\u2068";
const PDI = "\u2069";
const iso = (text) => FSI + text + PDI;

const KINDS = ["birthday", "yahrzeit", "anniversary", "custom"];
const KIND_ICONS = { birthday: "mdi:cake-variant", yahrzeit: "mdi:candle", anniversary: "mdi:ring", custom: "mdi:calendar-heart" };
const MONTHS = ["tishrei", "marcheshvan", "kislev", "tevet", "shvat", "adar", "adar_i", "adar_ii", "nisan", "iyyar", "sivan", "tammuz", "av", "elul"];
const MONTHS_29 = new Set(["tevet", "adar", "adar_ii", "iyyar", "tammuz", "elul"]);
const ADAR_MONTHS = new Set(["adar", "adar_i", "adar_ii"]);
const DAY30_MONTHS = new Set(["marcheshvan", "kislev", "adar_i"]);
const MAX_NAME = 100;
const MAX_NOTES = 500;
const REFRESH_MS = 10 * 60 * 1000;
const TIMER_DOMAINS = ["switch", "light", "input_boolean", "fan", "climate", "water_heater", "media_player",
  "humidifier", "scene", "siren", "vacuum"];

const I18N = {
  en: {
    title: "Good Days",
    tab_dates: "Family dates",
    tab_timers: "Shabbat timers",
    timers_status: "Timers status",
    timers_enabled: "Shabbat timers on",
    timers_skip: (p) => `Skip ${p}`,
    profile: "Profile",
    profile_default: "Regular",
    profiles_manage: "Profiles",
    profile_new: "New profile name",
    profile_new_hint: "For example Guests, Summer, Away.",
    profile_start: "Start with",
    profile_empty: "No timers",
    profile_copy: (p) => `A copy of ${p}`,
    profile_add: "Add profile",
    close: "Close",
    next_action: (when, name, act) => `Next: ${when} · ${name} (${act})`,
    next_action_named: (when, name) => `Next: ${when} · ${name}`,
    no_next_action: "No timer is scheduled.",
    period_skipped: "Skipped: nothing will run in this Shabbat / Chag.",
    no_actions: "No timers apply.",
    before_period: "before candle lighting",
    after_period: "after havdalah",
    done: "done",
    conflict: (t, w) => `Conflict: ${t} is turned on and off at ${w}.`,
    rules_title: (p) => `Timers · ${p}`,
    rules_empty: "No timers yet. Add one, or start from a preset (hot plate, urn, lights).",
    timer_add: "Add timer",
    timer_edit: "Edit timer",
    timer_preset: "From a preset",
    preset: "Preset",
    preset_hint: "Creates the on and the off timer; you can edit both.",
    preset_hot_plate: "Hot plate",
    preset_urn: "Water urn",
    preset_evening_lights: "Evening lights",
    preset_morning_lights: "Morning lights",
    preset_air_conditioner: "Air conditioner",
    targets: "Devices",
    targets_hint: "Switches, lights, plugs, AC, scenes...",
    action: "Turn",
    act_on: "On",
    act_off: "Off",
    anchor: "When",
    anchor_candle_lighting: "Around candle lighting",
    anchor_havdalah: "Around havdalah",
    anchor_clock: "At a time on each holy day",
    minutes: "Minutes",
    side: "Before / after",
    side_before: "Before",
    side_after: "After",
    time: "Time",
    time_hint: "Later than candle lighting (e.g. 23:00) is the evening before.",
    days: "Days",
    days_each: "Every day of Shabbat / Chag",
    days_first: "First day only",
    days_last: "Last day only",
    days_erev: "Erev (the day before)",
    at_candle_lighting: "at candle lighting",
    at_havdalah: "at havdalah",
    before_candle_lighting: (m) => `${iso(m)} min before candle lighting`,
    after_candle_lighting: (m) => `${iso(m)} min after candle lighting`,
    before_havdalah: (m) => `${iso(m)} min before havdalah`,
    after_havdalah: (m) => `${iso(m)} min after havdalah`,
    applies_to: "Applies to",
    kind_shabbat: "Shabbat",
    kind_yom_tov: "Yom Tov",
    kind_yom_kippur: "Yom Kippur",
    conditions: "Only if (optional)",
    conditions_hint: "Home Assistant conditions, checked when the timer fires.",
    has_conditions: (n) => `${iso(n)} condition(s)`,
    enabled: "Enabled",
    disabled: "off",
    run_now_on: "Turn on now",
    run_now_off: "Turn off now",
    run_now_named: (verb, n, t) => `${verb}: ${n} · ${t}`,
    profile_active: "Active profile",
    profile_view: "Show and edit:",
    profile_view_ro: "Show profile:",
    profile_is_active: "active",
    preview_profile: (p) => `Preview for profile: ${p}`,
    preview_not_active: (p) => `Preview for profile: ${p}. It is not the active profile, so these timers will not run.`,
    profile_timers: (n) => (n === 1 ? "1 timer" : `${iso(n)} timers`),
    rename: "Rename",
    rename_named: (n) => `Rename ${n}`,
    skip_hint: "Applies to this Shabbat / Chag only and clears itself afterwards.",
    wont_run: "won't run",
    readonly_notice: "Only Home Assistant admins can change timers. You can see here what will run.",
    instance_n: (title, n) => `${title} (${iso(n)})`,
    ran: "Done",
    run_failed: "Could not run it.",
    duplicate: "Duplicate",
    duplicate_named: (n) => `Duplicate ${n}`,
    history: "History",
    st_done: "done",
    st_late: "done late",
    st_skipped: "skipped",
    st_missed: "missed",
    st_failed: "failed",
    e_invalid_targets: "Pick at least one device.",
    e_unknown_targets: "One of the devices does not exist.",
    e_scene_off: "Scenes can only be turned on.",
    e_invalid_action: "Pick on or off.",
    e_invalid_anchor: "Pick when.",
    e_invalid_offset: "Minutes must be a whole number from 0 to 720.",
    e_invalid_time: "Enter a time as HH:MM.",
    e_invalid_days: "Pick the days.",
    e_invalid_applies_to: "Pick at least one: Shabbat, Yom Tov or Yom Kippur.",
    e_invalid_profile: "Pick a profile.",
    e_invalid_conditions: "One of the conditions is not valid.",
    e_too_many_rules: "Too many timers.",
    e_invalid_profile_name: "Use a new name, up to 40 characters.",

    add: "Add date",
    empty: "No family dates yet. Add birthdays, yahrzeits and anniversaries by their Hebrew date.",
    loading: "Loading…",
    load_error: "Could not load family dates.",
    not_loaded: "Good Days is not set up. Add it in Settings → Devices & services.",
    instance: "Instance",
    edit: "Edit",
    delete: "Delete",
    edit_named: (n) => `Edit ${n}`,
    delete_named: (n) => `Delete ${n}`,
    next: "Next",
    today: "Today",
    tomorrow: "Tomorrow",
    now: "Now",
    in_days: (n) => `in ${iso(n)} days`,
    on_shabbat: "On Shabbat / Yom Tov",
    dialog_add: "Add family date",
    dialog_edit: "Edit family date",
    name: "Name",
    kind: "Kind",
    date_mode: "Enter the date as",
    mode_hebrew: "Hebrew date",
    mode_gregorian: "Gregorian date",
    day: "Day",
    month: "Month",
    year: "Hebrew year (optional)",
    year_hint: "For example 5745, or in Hebrew letters תשמ״ה. Shows age or number of years.",
    year_parsed: (v) => `= ${v}`,
    gregorian_date: "Gregorian date",
    after_sunset: "After sunset (the Hebrew date had already changed)",
    converted: (d) => `Hebrew date: ${d}`,
    adar_rule: "In a leap year, observe in",
    adar_default: (m) => `Default (${m})`,
    day30_rule: "When the month has no 30th",
    notes: "Notes",
    remind: "Remind me",
    ics_title: "Calendar subscription",
    ics_enable: "Share family dates as a calendar link",
    ics_holidays: "Include Shabbat and holidays",
    ics_url: "Calendar link",
    ics_copy: "Copy link",
    ics_copied: "Link copied",
    ics_open: "Open in calendar app",
    ics_new: "New link (the old one stops working)",
    ics_hint: "Add it in Google Calendar (From URL) or on your phone. Anyone with the link can see the dates. Google needs a link that works from the internet (Home Assistant Cloud or an external URL).",
    ics_error: "Could not change the calendar link.",
    r_0: "On the day",
    r_0_yahrzeit: "The evening it begins (1 h before sunset)",
    r_1: "1 day before",
    r_n: (n) => `${n} days before`,
    remind_hint: "Where and when is set in Good Days options (notify targets, time).",
    save: "Save",
    cancel: "Cancel",
    confirm_delete: (n) => `Delete ${n}? This cannot be undone.`,
    saved: "Saved",
    deleted: "Deleted",
    save_error: "Could not save. Try again.",
    k_birthday: "Birthday",
    k_yahrzeit: "Yahrzeit",
    k_anniversary: "Anniversary",
    k_custom: "Other",
    a_adar_i: "Adar I",
    a_adar_ii: "Adar II",
    a_both: "Both",
    d_next: "1st of the next month",
    d_29: "29th of the same month",
    e_invalid_name: `Enter a name (up to ${MAX_NAME} characters).`,
    e_invalid_kind: "Pick a kind.",
    e_invalid_month: "Pick a month.",
    e_invalid_day: "This month has no such day.",
    e_invalid_year: "Enter a Hebrew year, e.g. 5745 or תשמ״ה (3000 to 6500).",
    e_invalid_date: "Enter a valid date.",
    e_invalid_notes: `Notes can be up to ${MAX_NOTES} characters.`,
    e_invalid_adar_rule: "Pick an option.",
    e_invalid_day30_rule: "Pick an option.",
    e_invalid_reminder_days: "Invalid reminder days.",
    e_not_found: "This date was deleted elsewhere.",
    e_too_many_dates: "Too many dates.",
    m_tishrei: "Tishrei", m_marcheshvan: "Cheshvan", m_kislev: "Kislev", m_tevet: "Tevet", m_shvat: "Shvat",
    m_adar: "Adar", m_adar_i: "Adar I", m_adar_ii: "Adar II", m_nisan: "Nisan", m_iyyar: "Iyar",
    m_sivan: "Sivan", m_tammuz: "Tammuz", m_av: "Av", m_elul: "Elul",
    m_adar_plain: "Adar (plain year)",
  },
  he: {
    title: "ימים טובים",
    tab_dates: "תאריכים משפחתיים",
    tab_timers: "טיימרים לשבת",
    timers_status: "מצב הטיימרים",
    timers_enabled: "טיימרים לשבת פעילים",
    timers_skip: (p) => `דילוג על ${p}`,
    profile: "פרופיל",
    profile_default: "רגיל",
    profiles_manage: "פרופילים",
    profile_new: "שם פרופיל חדש",
    profile_new_hint: "למשל אורחים, קיץ, לא בבית.",
    profile_start: "להתחיל עם",
    profile_empty: "בלי טיימרים",
    profile_copy: (p) => `עותק של ${p}`,
    profile_add: "הוספת פרופיל",
    close: "סגירה",
    next_action: (when, name, act) => `הבא: ${when} · ${name} (${act})`,
    next_action_named: (when, name) => `הבא: ${when} · ${name}`,
    no_next_action: "אין טיימר מתוזמן.",
    period_skipped: "דילוג: שום דבר לא יופעל בשבת / חג הזה.",
    no_actions: "אין טיימרים שחלים.",
    before_period: "לפני הדלקת נרות",
    after_period: "אחרי ההבדלה",
    done: "בוצע",
    conflict: (t, w) => `התנגשות: ${t} נדלק וכבה ב-${w}.`,
    rules_title: (p) => `טיימרים · ${p}`,
    rules_empty: "אין עדיין טיימרים. הוסיפו טיימר או התחילו מתבנית (פלטה, מיחם, תאורה).",
    timer_add: "הוספת טיימר",
    timer_edit: "עריכת טיימר",
    timer_preset: "מתבנית",
    preset: "תבנית",
    preset_hint: "יוצרת טיימר הדלקה וטיימר כיבוי; אפשר לערוך את שניהם.",
    preset_hot_plate: "פלטה",
    preset_urn: "מיחם",
    preset_evening_lights: "תאורת ערב",
    preset_morning_lights: "תאורת בוקר",
    preset_air_conditioner: "מזגן",
    targets: "מכשירים",
    targets_hint: "מתגים, אורות, שקעים, מזגן, סצנות...",
    action: "פעולה",
    act_on: "הדלקה",
    act_off: "כיבוי",
    anchor: "מתי",
    anchor_candle_lighting: "סביב הדלקת נרות",
    anchor_havdalah: "סביב ההבדלה",
    anchor_clock: "בשעה קבועה בכל יום של שבת / חג",
    minutes: "דקות",
    side: "לפני / אחרי",
    side_before: "לפני",
    side_after: "אחרי",
    time: "שעה",
    time_hint: "שעה מאוחרת מהדלקת הנרות (למשל 23:00) היא בערב שלפני.",
    days: "ימים",
    days_each: "בכל יום של שבת / חג",
    days_first: "רק ביום הראשון",
    days_last: "רק ביום האחרון",
    days_erev: "בערב שבת / חג (היום שלפני)",
    at_candle_lighting: "בהדלקת נרות",
    at_havdalah: "בהבדלה",
    before_candle_lighting: (m) => `${iso(m)} דק׳ לפני הדלקת נרות`,
    after_candle_lighting: (m) => `${iso(m)} דק׳ אחרי הדלקת נרות`,
    before_havdalah: (m) => `${iso(m)} דק׳ לפני ההבדלה`,
    after_havdalah: (m) => `${iso(m)} דק׳ אחרי ההבדלה`,
    applies_to: "חל על",
    kind_shabbat: "שבת",
    kind_yom_tov: "יום טוב",
    kind_yom_kippur: "יום כיפור",
    conditions: "רק אם (רשות)",
    conditions_hint: "תנאים של Home Assistant, נבדקים ברגע ההפעלה.",
    has_conditions: (n) => `${iso(n)} תנאים`,
    enabled: "פעיל",
    disabled: "מושבת",
    run_now_on: "להדליק עכשיו",
    run_now_off: "לכבות עכשיו",
    run_now_named: (verb, n, t) => `${verb}: ${n} · ${t}`,
    profile_active: "פרופיל פעיל",
    profile_view: "הצגה ועריכה:",
    profile_view_ro: "הצגת פרופיל:",
    profile_is_active: "פעיל",
    preview_profile: (p) => `תצוגה מקדימה לפי פרופיל: ${p}`,
    preview_not_active: (p) => `תצוגה מקדימה לפי פרופיל: ${p}. זה לא הפרופיל הפעיל, ולכן הטיימרים האלה לא יופעלו.`,
    profile_timers: (n) => (n === 1 ? "טיימר אחד" : `${iso(n)} טיימרים`),
    rename: "שינוי שם",
    rename_named: (n) => `שינוי שם: ${n}`,
    skip_hint: "חל רק על השבת / החג הזה, ומתבטל מעצמו אחריו.",
    wont_run: "לא יופעל",
    readonly_notice: "רק מנהלי Home Assistant יכולים לשנות טיימרים. אפשר לראות כאן מה יופעל.",
    instance_n: (title, n) => `${title} (${iso(n)})`,
    ran: "בוצע",
    run_failed: "ההפעלה נכשלה.",
    duplicate: "שכפול",
    duplicate_named: (n) => `שכפול ${n}`,
    history: "היסטוריה",
    st_done: "בוצע",
    st_late: "בוצע באיחור",
    st_skipped: "דולג",
    st_missed: "הוחמץ",
    st_failed: "נכשל",
    e_invalid_targets: "יש לבחור לפחות מכשיר אחד.",
    e_unknown_targets: "אחד המכשירים לא קיים.",
    e_scene_off: "סצנה אפשר רק להפעיל.",
    e_invalid_action: "יש לבחור הדלקה או כיבוי.",
    e_invalid_anchor: "יש לבחור מתי.",
    e_invalid_offset: "מספר הדקות חייב להיות מספר שלם בין 0 ל-720.",
    e_invalid_time: "יש להזין שעה בפורמט HH:MM.",
    e_invalid_days: "יש לבחור ימים.",
    e_invalid_applies_to: "יש לבחור לפחות אחד: שבת, יום טוב או יום כיפור.",
    e_invalid_profile: "יש לבחור פרופיל.",
    e_invalid_conditions: "אחד התנאים אינו תקין.",
    e_too_many_rules: "יותר מדי טיימרים.",
    e_invalid_profile_name: "יש להזין שם חדש, עד 40 תווים.",

    add: "הוספת תאריך",
    empty: "אין עדיין תאריכים משפחתיים. הוסיפו ימי הולדת, ימי השנה וימי נישואין לפי התאריך העברי.",
    loading: "טוען…",
    load_error: "לא ניתן לטעון את התאריכים.",
    not_loaded: "ימים טובים לא מוגדר. הוסיפו אותו בהגדרות ← מכשירים ושירותים.",
    instance: "מופע",
    edit: "עריכה",
    delete: "מחיקה",
    edit_named: (n) => `עריכת ${n}`,
    delete_named: (n) => `מחיקת ${n}`,
    next: "המועד הבא",
    today: "היום",
    tomorrow: "מחר",
    now: "עכשיו",
    in_days: (n) => (n === 2 ? "בעוד יומיים" : `בעוד ${iso(n)} ימים`),
    on_shabbat: "חל בשבת / חג",
    dialog_add: "הוספת תאריך משפחתי",
    dialog_edit: "עריכת תאריך משפחתי",
    name: "שם",
    kind: "סוג",
    date_mode: "הזנת התאריך לפי",
    mode_hebrew: "תאריך עברי",
    mode_gregorian: "תאריך לועזי",
    day: "יום",
    month: "חודש",
    year: "שנה עברית (רשות)",
    year_hint: "למשל תשמ״ה או 5745. מציג גיל או מספר שנים.",
    year_parsed: (v) => `כלומר ${v}`,
    gregorian_date: "תאריך לועזי",
    after_sunset: "אחרי השקיעה (התאריך העברי כבר התחלף)",
    converted: (d) => `תאריך עברי: ${d}`,
    adar_rule: "בשנה מעוברת, לציין ב",
    adar_default: (m) => `ברירת מחדל (${m})`,
    day30_rule: "כשאין בחודש יום ל׳",
    notes: "הערות",
    remind: "להזכיר",
    ics_title: "מינוי ללוח שנה",
    ics_enable: "לשתף את התאריכים המשפחתיים כקישור ללוח שנה",
    ics_holidays: "לכלול שבתות וחגים",
    ics_url: "קישור ללוח השנה",
    ics_copy: "העתקת הקישור",
    ics_copied: "הקישור הועתק",
    ics_open: "פתיחה באפליקציית היומן",
    ics_new: "קישור חדש (הישן יפסיק לעבוד)",
    ics_hint: "הוסיפו ב-Google Calendar (מכתובת URL) או בטלפון. כל מי שיש לו את הקישור יכול לראות את התאריכים. Google צריך קישור שעובד מהאינטרנט (Home Assistant Cloud או כתובת חיצונית).",
    ics_error: "לא ניתן לשנות את קישור לוח השנה.",
    r_0: "ביום עצמו",
    r_0_yahrzeit: "בערב שבו הוא מתחיל (שעה לפני השקיעה)",
    r_1: "יום לפני",
    r_n: (n) => `${n} ימים לפני`,
    remind_hint: "לאן ובאיזו שעה נקבע באפשרויות של ימים טובים (יעדי התראה, שעה).",
    save: "שמירה",
    cancel: "ביטול",
    confirm_delete: (n) => `למחוק את ${n}? אי אפשר לבטל.`,
    saved: "נשמר",
    deleted: "נמחק",
    save_error: "השמירה נכשלה. נסו שוב.",
    k_birthday: "יום הולדת",
    k_yahrzeit: "יום השנה",
    k_anniversary: "יום נישואין",
    k_custom: "אחר",
    a_adar_i: "אדר א׳",
    a_adar_ii: "אדר ב׳",
    a_both: "שניהם",
    d_next: "א׳ בחודש הבא",
    d_29: "כ״ט באותו חודש",
    e_invalid_name: `יש להזין שם (עד ${MAX_NAME} תווים).`,
    e_invalid_kind: "יש לבחור סוג.",
    e_invalid_month: "יש לבחור חודש.",
    e_invalid_day: "אין יום כזה בחודש הזה.",
    e_invalid_year: "יש להזין שנה עברית, למשל תשמ״ה או 5745 (בין 3000 ל-6500).",
    e_invalid_date: "יש להזין תאריך תקין.",
    e_invalid_notes: `הערות עד ${MAX_NOTES} תווים.`,
    e_invalid_adar_rule: "יש לבחור אפשרות.",
    e_invalid_day30_rule: "יש לבחור אפשרות.",
    e_invalid_reminder_days: "ימי תזכורת לא תקינים.",
    e_not_found: "התאריך נמחק במקום אחר.",
    e_too_many_dates: "יותר מדי תאריכים.",
    m_tishrei: "תשרי", m_marcheshvan: "חשוון", m_kislev: "כסלו", m_tevet: "טבת", m_shvat: "שבט",
    m_adar: "אדר", m_adar_i: "אדר א׳", m_adar_ii: "אדר ב׳", m_nisan: "ניסן", m_iyyar: "אייר",
    m_sivan: "סיוון", m_tammuz: "תמוז", m_av: "אב", m_elul: "אלול",
    m_adar_plain: "אדר (שנה פשוטה)",
  },
};

function langOf(hass) {
  const lang = (hass && ((hass.locale && hass.locale.language) || hass.language)) || "en";
  return String(lang).toLowerCase().startsWith("he") ? "he" : "en";
}

function mk(tag, cls, text) {
  const el = document.createElement(tag);
  if (cls) el.className = cls;
  if (text != null) el.textContent = text;
  return el;
}

// Hebrew numerals for days 1-30 (ט״ו / ט״ז, not יה / יו).
function gematriaDay(n) {
  const units = ["", "א", "ב", "ג", "ד", "ה", "ו", "ז", "ח", "ט"];
  const tens = ["", "י", "כ", "ל"];
  let letters = n === 15 ? "טו" : n === 16 ? "טז" : tens[Math.floor(n / 10)] + units[n % 10];
  return letters.length > 1 ? `${letters.slice(0, -1)}״${letters.slice(-1)}` : `${letters}׳`;
}

// The first keyboard-focusable element inside `host`, searching open shadow roots in render order.
function deepFocusable(host) {
  const visit = (node) => {
    for (const el of node.children || []) {
      if (el.tabIndex >= 0 && !el.disabled && !el.hasAttribute("aria-hidden") && el.getClientRects().length) return el;
      const found = (el.shadowRoot && visit(el.shadowRoot)) || visit(el);
      if (found) return found;
    }
    return null;
  };
  return host.shadowRoot ? visit(host.shadowRoot) : null;
}

const LETTER_VALUES = {
  "א": 1, "ב": 2, "ג": 3, "ד": 4, "ה": 5, "ו": 6, "ז": 7, "ח": 8, "ט": 9,
  "י": 10, "כ": 20, "ך": 20, "ל": 30, "מ": 40, "ם": 40, "נ": 50, "ן": 50, "ס": 60, "ע": 70, "פ": 80, "ף": 80,
  "צ": 90, "ץ": 90, "ק": 100, "ר": 200, "ש": 300, "ת": 400,
};

// A Hebrew year as typed: digits (5770) or letters (תש״ע, תשע, ה׳תש״ע, התש"ע). Returns a number, or null when
// the text is not a year at all. Letters without the thousands are taken as the 6th millennium (5000s).
function parseHebrewYear(text) {
  const raw = String(text || "").trim();
  if (/^\d+$/.test(raw)) return Number(raw);
  const letters = raw.replace(/[\s'"׳״`.׳״-]/g, "");
  if (!letters || [...letters].some((ch) => !LETTER_VALUES[ch])) return null;
  const values = [...letters].map((ch) => LETTER_VALUES[ch]);
  let thousands = 5;
  // "ה׳תש״ע": a leading letter (1-9) followed by a larger one is the thousands; letters otherwise run high to low.
  if (values.length > 1 && values[0] < 10 && values[0] < values[1]) thousands = values.shift();
  else if (/^[א-ט]['׳]/.test(raw) && values.length > 1) thousands = values.shift();
  for (let i = 1; i < values.length; i += 1) if (values[i] > values[i - 1]) return null;
  const units = values.reduce((a, b) => a + b, 0);
  return units >= 1000 ? null : thousands * 1000 + units;
}

// 5770 -> תש״ע (the year within the millennium, as printed on calendars and stones).
function gematriaYear(year) {
  let n = year % 1000;
  let letters = "";
  [[400, "ת"], [300, "ש"], [200, "ר"], [100, "ק"]].forEach(([v, ch]) => { while (n >= v) { letters += ch; n -= v; } });
  if (n === 15 || n === 16) letters += n === 15 ? "טו" : "טז";
  else {
    const tens = ["", "י", "כ", "ל", "מ", "נ", "ס", "ע", "פ", "צ"];
    const units = ["", "א", "ב", "ג", "ד", "ה", "ו", "ז", "ח", "ט"];
    letters += tens[Math.floor(n / 10)] + units[n % 10];
  }
  if (!letters) return String(year);
  return letters.length > 1 ? `${letters.slice(0, -1)}״${letters.slice(-1)}` : `${letters}׳`;
}

const STYLE = `
  [hidden] { display: none !important; }
  :host { display: block; min-height: 100vh; background: var(--primary-background-color); color: var(--primary-text-color);
    font-family: var(--paper-font-body1_-_font-family, Roboto, sans-serif);
    /* Readable variants of the theme colours (WCAG 1.4.3 / 1.4.11): theme accents are fills, too light as text on
       Home Assistant's default themes. Mixed toward the text colour, so they darken on light and lighten on dark. */
    --gd-accent-text: color-mix(in srgb, var(--primary-color) 70%, var(--primary-text-color));
    --gd-accent-fill: color-mix(in srgb, var(--primary-color) 80%, black);
    --gd-error-text: color-mix(in srgb, var(--error-color, #db4437) 75%, var(--primary-text-color));
    --gd-warning-text: color-mix(in srgb, var(--warning-color, #ff9800) 50%, var(--primary-text-color));
    --gd-field-border: color-mix(in srgb, var(--secondary-text-color) 80%, transparent); }
  .toolbar { display: flex; align-items: center; gap: 8px; height: var(--header-height, 56px); padding: 0 12px;
    background: var(--app-header-background-color, var(--primary-color)); color: var(--app-header-text-color, #fff);
    box-sizing: border-box; }
  .toolbar h1 { flex: 1; font-size: 20px; font-weight: 400; margin: 0; }
  .toolbar select { font: inherit; padding: 4px 8px; border-radius: 6px; width: auto; max-width: 50%; }
  main { max-width: 760px; margin: 0 auto; padding: 16px; box-sizing: border-box; }
  .actions { display: flex; justify-content: flex-end; margin-bottom: 12px; }
  button { font: inherit; cursor: pointer; }
  button.primary { background: var(--gd-accent-fill); color: #fff; border: none; border-radius: 8px;
    padding: 8px 16px; display: inline-flex; align-items: center; gap: 6px; }
  button.text { background: none; border: none; color: var(--gd-accent-text); padding: 6px 10px; border-radius: 6px; }
  button.danger { color: var(--gd-error-text); }
  button:focus-visible, input:focus-visible, select:focus-visible, textarea:focus-visible {
    outline: 2px solid var(--primary-color); outline-offset: 2px; }
  .card { background: var(--card-background-color); border-radius: 12px; box-shadow: var(--ha-card-box-shadow, 0 1px 3px rgba(0,0,0,.2)); }
  ul.dates { list-style: none; margin: 0; padding: 0; }
  ul.dates li { display: flex; align-items: center; gap: 12px; padding: 12px 16px; border-bottom: 1px solid var(--divider-color); }
  ul.dates li:last-child { border-bottom: none; }
  ha-icon.kind { color: var(--secondary-text-color); flex: none; }
  .info { flex: 1; min-width: 0; display: grid; gap: 2px; }
  .name { font-weight: 500; white-space: normal; overflow-wrap: anywhere; }
  .sub { font-size: 0.85rem; color: var(--secondary-text-color); display: flex; flex-wrap: wrap; gap: 4px 10px; }
  .chip { font-size: 0.78rem; padding: 2px 8px; border-radius: 999px; background: var(--secondary-background-color); white-space: nowrap; }
  .chip.now { background: var(--gd-accent-fill); color: #fff; }
  .conflict { color: var(--gd-warning-text); }
  .row-actions { display: flex; gap: 2px; flex: none; }
  .tabs { display: flex; gap: 4px; border-bottom: 1px solid var(--divider-color); margin-bottom: 16px; }
  .tab { background: none; border: none; border-bottom: 3px solid transparent; padding: 10px 14px; font: inherit;
    color: var(--secondary-text-color); cursor: pointer; }
  .tab[aria-selected=true] { color: var(--gd-accent-text); border-bottom-color: var(--gd-accent-text); font-weight: 500; }
  .tab:focus-visible { outline: 2px solid var(--primary-color); outline-offset: -2px; }
  .card.timers-status, .card.preview, .card.rules, .card.history { padding: 16px; margin-bottom: 16px; display: grid; gap: 10px; }
  .card.preview h2, .card.rules h2 { margin: 0; font-size: 1.05rem; font-weight: 500; }
  .card.preview p { margin: 0; }
  .row-inline { display: flex; flex-wrap: wrap; align-items: center; gap: 8px; }
  .row-inline select { width: auto; }
  .rules-head { display: flex; flex-wrap: wrap; align-items: center; justify-content: space-between; gap: 8px; }
  .rules-head h2 { flex: 1; }
  ol.timeline { list-style: none; margin: 0; padding: 0; display: grid; gap: 6px; }
  ol.timeline li { display: flex; flex-wrap: wrap; align-items: baseline; gap: 6px 10px; }
  ol.timeline li.done { color: var(--secondary-text-color); }
  ol.timeline li.skipped .time, ol.timeline li.skipped .what { color: var(--secondary-text-color); text-decoration: line-through; }
  ol.timeline .act.skip { background: none; border: 1px solid var(--gd-field-border); }
  .notice { margin: 0 0 16px; padding: 12px 16px; border-radius: 12px; background: var(--secondary-background-color);
    border-inline-start: 4px solid var(--gd-accent-text); }
  .profile-view { display: flex; flex-wrap: wrap; align-items: center; gap: 6px; }
  .profile-view .label { font-size: 0.85rem; color: var(--secondary-text-color); }
  .profile-view button { border: 1px solid var(--gd-field-border); background: none; color: var(--primary-text-color);
    border-radius: 999px; padding: 4px 12px; }
  .profile-view button[aria-pressed=true] { background: var(--gd-accent-fill); border-color: var(--gd-accent-fill); color: #fff; }
  .year-echo { color: var(--secondary-text-color); font-size: 0.8rem; }
  ol.timeline .time { font-variant-numeric: tabular-nums; min-width: 7em; }
  ol.timeline .act { font-size: 0.78rem; padding: 1px 8px; border-radius: 999px; background: var(--secondary-background-color); }
  ol.timeline .act.on { background: color-mix(in srgb, var(--success-color, #43a047) 18%, transparent); }
  .badge-soft { font-size: 0.75rem; color: var(--secondary-text-color); border: 1px solid var(--divider-color); border-radius: 999px; padding: 0 6px; }
  .warn { color: var(--gd-warning-text); margin: 0; }
  ul.dates li.disabled .name { color: var(--secondary-text-color); }
  details.history summary { cursor: pointer; font-weight: 500; }
  ul.history-list { margin: 8px 0 0; padding-inline-start: 18px; font-size: 0.85rem; display: grid; gap: 2px; }
  .st-failed, .st-missed { color: var(--gd-error-text); }
  ul.profile-list { list-style: none; margin: 0; padding: 0; display: grid; gap: 4px; }
  ul.profile-list li { display: flex; justify-content: space-between; align-items: center; }
  .card.ics { margin-top: 16px; padding: 16px; display: grid; gap: 10px; }
  .card.ics h2 { margin: 0; font-size: 1.05rem; font-weight: 500; }
  .ics-buttons { display: flex; flex-wrap: wrap; gap: 4px; }
  a.text { color: var(--gd-accent-text); padding: 6px 10px; text-decoration: none; border-radius: 6px; }
  a.text:focus-visible { outline: 2px solid var(--primary-color); outline-offset: 2px; }
  .empty, .status { padding: 24px 16px; color: var(--secondary-text-color); }
  .status.error { color: var(--gd-error-text); }
  dialog { border: none; border-radius: 16px; padding: 0; width: min(520px, calc(100vw - 32px)); max-height: calc(100vh - 32px);
    background: var(--card-background-color); color: var(--primary-text-color); box-shadow: 0 8px 32px rgba(0,0,0,.3); }
  dialog::backdrop { background: rgba(0,0,0,.4); }
  form { display: grid; gap: 14px; padding: 20px; }
  form h2 { margin: 0; font-size: 1.2rem; font-weight: 500; }
  .field { display: grid; gap: 4px; }
  .field label, fieldset legend { font-size: 0.85rem; color: var(--secondary-text-color); }
  input, select, textarea { font: inherit; padding: 8px 10px; border-radius: 8px; border: 1px solid var(--gd-field-border);
    background: var(--card-background-color); color: var(--primary-text-color); box-sizing: border-box; width: 100%; }
  input[type=checkbox], input[type=radio] { width: auto; }
  [aria-invalid=true] { border-color: var(--gd-error-text); }
  .err { color: var(--gd-error-text); font-size: 0.8rem; min-height: 0; }
  .hint { color: var(--secondary-text-color); font-size: 0.8rem; }
  .row3 { display: grid; grid-template-columns: 1fr 2fr 1.5fr; gap: 10px; }
  fieldset { border: none; margin: 0; padding: 0; display: flex; flex-wrap: wrap; gap: 6px 16px; }
  fieldset label, .check { display: inline-flex; align-items: center; gap: 6px; font-size: 0.95rem; color: var(--primary-text-color); }
  .buttons { display: flex; justify-content: flex-end; gap: 8px; }
  .toast { position: fixed; bottom: 16px; inset-inline-start: 50%; transform: translateX(-50%); background: #323232; color: #fff;
    padding: 10px 16px; border-radius: 8px; font-size: 0.9rem; }
  :host([dir=rtl]) .toast { transform: translateX(50%); }
  @media (max-width: 600px) {
    .row3 { grid-template-columns: 1fr 1fr; } .row3 .field.year { grid-column: 1 / -1; }
    /* Phones: name and details get the full width; countdown and buttons go below. */
    ul.dates li { flex-wrap: wrap; row-gap: 4px; }
    ul.dates .info { flex: 1 1 calc(100% - 36px); }
    ul.dates .name { white-space: normal; }
    ul.dates .chip { margin-inline-start: 32px; }
    ul.dates .row-actions { margin-inline-start: auto; }
  }
`;

class GoodDaysPanel extends HTMLElement {
  constructor() {
    super();
    this.attachShadow({ mode: "open" });
    this._dates = null;
    this._entries = [];
    this._entryId = null;
    this._error = null;
    this._timers = null;
    let tab = "dates";
    try { tab = localStorage.getItem("good_days_tab") || "dates"; } catch (err) { /* private mode */ }
    this._tab = tab === "timers" ? "timers" : "dates";
  }

  set hass(hass) {
    const first = !this._hass;
    const langChanged = this._hass && langOf(this._hass) !== langOf(hass);
    this._hass = hass;
    if (first) this._init();
    else if (langChanged) this._load();
    const menu = this.shadowRoot.querySelector("ha-menu-button");
    if (menu) menu.hass = hass;
  }

  set narrow(value) {
    this._narrow = value;
    const menu = this.shadowRoot.querySelector("ha-menu-button");
    if (menu) menu.narrow = value;
  }

  connectedCallback() {
    this._timer = setInterval(() => { if (!document.hidden) this._load(); }, REFRESH_MS);
  }

  disconnectedCallback() {
    clearInterval(this._timer);
  }

  _t(key, ...args) {
    const dict = I18N[langOf(this._hass)];
    const value = dict[key] != null ? dict[key] : I18N.en[key];
    return typeof value === "function" ? value(...args) : value;
  }

  async _init() {
    try {
      const res = await this._hass.callWS({ type: "good_days/entries", language: langOf(this._hass) });
      this._entries = (res && res.entries) || [];
    } catch (e) {
      try {
        const entries = await this._hass.callWS({ type: "config_entries/get", domain: "good_days" });
        this._entries = (entries || []).filter((e2) => e2.state === "loaded");
      } catch (e2) {
        this._entries = [];
      }
    }
    if (this._entries.length) this._entryId = this._entries[0].entry_id;
    await this._load();
  }

  _isAdmin() {
    return !!(this._hass && this._hass.user && this._hass.user.is_admin);
  }

  async _loadIcs() {
    if (!this._isAdmin()) { this._ics = null; return; }
    const msg = { type: "good_days/ics/get" };
    if (this._entryId) msg.entry_id = this._entryId;
    try {
      this._ics = await this._hass.callWS(msg);
    } catch (err) {
      this._ics = null;
    }
  }

  async _setIcs(patch) {
    const current = this._ics || { enabled: false, holidays: false };
    const msg = { type: "good_days/ics/set", enabled: current.enabled, holidays: current.holidays, ...patch };
    if (this._entryId) msg.entry_id = this._entryId;
    try {
      this._ics = await this._hass.callWS(msg);
    } catch (err) {
      this._toast(this._t("ics_error"));
    }
    this._render();
  }

  _icsUrl() {
    if (!this._ics || !this._ics.path) return "";
    if (this._ics.url) return this._ics.url;
    return this._hass.hassUrl ? this._hass.hassUrl(this._ics.path) : `${location.origin}${this._ics.path}`;
  }

  _renderIcs(main) {
    if (!this._isAdmin() || !this._ics) return;
    const card = mk("section", "card ics");
    card.setAttribute("aria-labelledby", "ics-title");
    const title = mk("h2", null, this._t("ics_title"));
    title.id = "ics-title";
    card.appendChild(title);

    const toggle = (key, checked, text, onChange) => {
      const label = mk("label", "check");
      const box = mk("input");
      box.type = "checkbox";
      box.checked = checked;
      box.setAttribute("data-focus-key", key);
      box.addEventListener("change", () => onChange(box.checked));
      label.append(box, mk("span", null, text));
      return label;
    };
    card.appendChild(toggle("ics-enable", this._ics.enabled, this._t("ics_enable"), (on) => this._setIcs({ enabled: on })));
    if (this._ics.enabled) {
      card.appendChild(toggle("ics-holidays", this._ics.holidays, this._t("ics_holidays"), (on) => this._setIcs({ holidays: on })));
      const url = this._icsUrl();
      const field = mk("div", "field");
      const label = mk("label", null, this._t("ics_url"));
      label.htmlFor = "ics-url";
      const input = mk("input");
      input.id = "ics-url";
      input.readOnly = true;
      input.value = url;
      input.dir = "ltr";
      input.setAttribute("data-focus-key", "ics-url");
      input.addEventListener("focus", () => input.select());
      field.append(label, input);
      card.appendChild(field);

      const buttons = mk("div", "ics-buttons");
      const copy = mk("button", "text", this._t("ics_copy"));
      copy.type = "button";
      copy.setAttribute("data-focus-key", "ics-copy");
      copy.addEventListener("click", async () => {
        try {
          await navigator.clipboard.writeText(url);
          this._toast(this._t("ics_copied"));
        } catch (err) {
          input.focus();
        }
      });
      const open = mk("a", "text", this._t("ics_open"));
      open.href = url.replace(/^https?:/, "webcal:");
      const fresh = mk("button", "text danger", this._t("ics_new"));
      fresh.type = "button";
      fresh.setAttribute("data-focus-key", "ics-new");
      fresh.addEventListener("click", () => this._setIcs({ new_link: true }));
      buttons.append(copy, open, fresh);
      card.appendChild(buttons);
      card.appendChild(mk("p", "hint", this._t("ics_hint")));
    }
    main.appendChild(card);
  }

  async _load() {
    if (!this._hass) return;
    await Promise.all([this._loadIcs(), this._loadTimers()]);
    const msg = { type: "good_days/dates/list", language: langOf(this._hass) };
    if (this._entryId) msg.entry_id = this._entryId;
    try {
      const result = await this._hass.callWS(msg);
      this._dates = result.dates;
      this._error = null;
    } catch (err) {
      this._error = err && err.code === "not_loaded" ? "not_loaded" : "load_error";
    }
    // Periodic refreshes usually bring back the same data: keep the page (and focus, scroll) as it is.
    if (this._stateSig() === this._renderedSig) return;
    this._render();
  }

  _stateSig() {
    return JSON.stringify([langOf(this._hass), this._isAdmin(), this._entryId, this._tab, this._error, this._dates, this._timers, this._ics]);
  }

  _monthLabel(month, plain) {
    if (month === "adar" && plain) return this._t("m_adar_plain");
    return this._t(`m_${month}`);
  }

  _hebrewLabel(record) {
    const he = langOf(this._hass) === "he";
    const day = he ? gematriaDay(record.hebrew_day) : String(record.hebrew_day);
    return `${day} ${this._monthLabel(record.hebrew_month)}`;
  }

  _countdown(next) {
    if (next.in_effect) return { text: this._t("now"), now: true };
    if (next.days_until <= 0) return { text: this._t("today"), now: false };
    if (next.days_until === 1) return { text: this._t("tomorrow"), now: false };
    return { text: this._t("in_days", next.days_until), now: false };
  }

  _gregorian(next) {
    const locale = langOf(this._hass) === "he" ? "he-IL" : (this._hass.locale && this._hass.locale.language) || "en";
    const day = (next.day || next.start).slice(0, 10); // yahrzeit: the day itself, not the evening before
    const date = new Date(Date.UTC(+day.slice(0, 4), +day.slice(5, 7) - 1, +day.slice(8, 10), 12));
    return date.toLocaleDateString(locale, { weekday: "short", day: "numeric", month: "short", year: "numeric", timeZone: "UTC" });
  }

  // Rendering ---------------------------------------------------------------

  _render() {
    const active = this.shadowRoot.activeElement;
    let focusKey = active ? active.getAttribute("data-focus-key") : null;
    const lang = langOf(this._hass);
    const root = this.shadowRoot;
    const dialogOpen = root.querySelector("dialog[open]");
    if (dialogOpen) return; // never rebuild under an open dialog
    if (this._returnFocus) {
      focusKey = this._returnFocus; // a dialog just closed: back to the control that opened it
      this._returnFocus = null;
    }
    const toast = root.querySelector(".toast");
    this._renderedSig = this._stateSig();
    root.textContent = "";
    this.setAttribute("dir", lang === "he" ? "rtl" : "ltr");
    this.setAttribute("lang", lang);
    root.appendChild(mk("style", null, STYLE));
    if (toast) root.appendChild(toast);

    const toolbar = mk("div", "toolbar");
    const menu = document.createElement("ha-menu-button");
    menu.hass = this._hass;
    menu.narrow = this._narrow;
    toolbar.appendChild(menu);
    toolbar.appendChild(mk("h1", null, this._t("title")));
    if (this._entries.length > 1) {
      const select = mk("select");
      select.setAttribute("aria-label", this._t("instance"));
      select.setAttribute("data-focus-key", "instance");
      // Every entry is titled "Good Days" unless renamed: number the ones that share a title.
      const counts = {};
      this._entries.forEach((e) => { counts[e.title] = (counts[e.title] || 0) + 1; });
      const seen = {};
      this._entries.forEach((e) => {
        seen[e.title] = (seen[e.title] || 0) + 1;
        const text = e.label || (counts[e.title] > 1 ? this._t("instance_n", e.title, seen[e.title]) : e.title);
        select.appendChild(new Option(text, e.entry_id));
      });
      select.value = this._entryId;
      select.addEventListener("change", () => { this._entryId = select.value; this._shownProfile = null; this._load(); });
      toolbar.appendChild(select);
    }
    root.appendChild(toolbar);

    const main = mk("main");
    root.appendChild(main);
    this._renderTabs(main);
    const panel = mk("div");
    panel.id = `panel-${this._tab}`;
    panel.setAttribute("role", "tabpanel");
    panel.setAttribute("aria-labelledby", `tab-${this._tab}`);
    main.appendChild(panel);
    if (this._tab === "timers") this._renderTimers(panel);
    else this._renderMainAndIcs(panel);
    if (focusKey) {
      const again = root.querySelector(`[data-focus-key="${CSS.escape(focusKey)}"]`);
      if (again) again.focus();
    }
  }

  _renderMain(main) {
    if (this._error) {
      main.appendChild(mk("p", "status error", this._t(this._error)));
      return;
    }
    const actions = mk("div", "actions");
    const add = mk("button", "primary");
    add.type = "button";
    add.setAttribute("data-focus-key", "add");
    const plus = document.createElement("ha-icon");
    plus.setAttribute("icon", "mdi:plus");
    plus.setAttribute("aria-hidden", "true");
    add.append(plus, mk("span", null, this._t("add")));
    add.addEventListener("click", () => this._openEditor(null, add));
    actions.appendChild(add);
    main.appendChild(actions);

    const card = mk("div", "card");
    main.appendChild(card);
    if (this._dates == null) {
      card.appendChild(mk("p", "status", this._t("loading")));
      return;
    }
    if (!this._dates.length) {
      card.appendChild(mk("p", "empty", this._t("empty")));
      return;
    }
    const list = mk("ul", "dates");
    list.setAttribute("aria-label", this._t("tab_dates"));
    // Reuse the rows whose data did not change (a save or delete touches one row; up to 500 are listed).
    const lang = langOf(this._hass);
    const old = this._rowCache || new Map();
    const cache = new Map();
    this._dates.forEach((record) => {
      const key = lang + JSON.stringify(record);
      const hit = old.get(record.id);
      const li = hit && hit.key === key ? hit.li : this._renderRow(record);
      cache.set(record.id, { key, li });
      list.appendChild(li);
    });
    this._rowCache = cache;
    card.appendChild(list);
  }

  _renderMainAndIcs(main) {
    this._renderMain(main);
    if (!this._error) this._renderIcs(main);
  }

  _renderRow(record) {
    const li = mk("li");
    const icon = document.createElement("ha-icon");
    icon.className = "kind";
    icon.setAttribute("icon", KIND_ICONS[record.kind] || KIND_ICONS.custom);
    icon.setAttribute("aria-hidden", "true");
    li.appendChild(icon);

    const info = mk("div", "info");
    info.appendChild(mk("span", "name", record.next ? record.next.title : record.name));
    const sub = mk("span", "sub");
    sub.appendChild(mk("span", null, `${this._t(`k_${record.kind}`)} · ${this._hebrewLabel(record)}`));
    if (record.next) {
      sub.appendChild(mk("span", null, `${this._t("next")}: ${this._gregorian(record.next)}`));
      if (record.next.conflicts_shabbat) sub.appendChild(mk("span", "conflict", `⚠ ${this._t("on_shabbat")}`));
    }
    info.appendChild(sub);
    li.appendChild(info);

    if (record.next) {
      const cd = this._countdown(record.next);
      li.appendChild(mk("span", cd.now ? "chip now" : "chip", cd.text));
    }

    const actions = mk("div", "row-actions");
    const edit = mk("button", "text", this._t("edit"));
    edit.type = "button";
    edit.setAttribute("aria-label", this._t("edit_named", record.name));
    edit.setAttribute("data-focus-key", `edit-${record.id}`);
    edit.addEventListener("click", () => this._openEditor(record, edit));
    const del = mk("button", "text danger", this._t("delete"));
    del.type = "button";
    del.setAttribute("aria-label", this._t("delete_named", record.name));
    del.setAttribute("data-focus-key", `delete-${record.id}`);
    del.addEventListener("click", () => this._confirmDelete(record, del));
    actions.append(edit, del);
    li.appendChild(actions);
    return li;
  }

  _toast(text) {
    const old = this.shadowRoot.querySelector(".toast");
    if (old) old.remove();
    const toast = mk("div", "toast", text);
    toast.setAttribute("role", "status");
    this.shadowRoot.appendChild(toast);
    setTimeout(() => toast.remove(), 3000);
  }

  _baseMsg(type) {
    const msg = { type, language: langOf(this._hass) };
    if (this._entryId) msg.entry_id = this._entryId;
    return msg;
  }

  // Delete ------------------------------------------------------------------

  _confirmDelete(record, opener) {
    const dialog = mk("dialog");
    dialog.setAttribute("aria-labelledby", "confirm-title");
    const form = mk("form");
    form.method = "dialog";
    const title = mk("h2", null, this._t("confirm_delete", record.name));
    title.id = "confirm-title";
    const buttons = mk("div", "buttons");
    const cancel = mk("button", "text", this._t("cancel"));
    cancel.type = "button";
    cancel.addEventListener("click", () => dialog.dismiss(false));
    const ok = mk("button", "primary", this._t("delete"));
    ok.type = "submit";
    buttons.append(cancel, ok);
    form.append(title, buttons);
    dialog.appendChild(form);
    form.addEventListener("submit", async (ev) => {
      ev.preventDefault();
      ok.disabled = true;
      try {
        const msg = this._baseMsg("good_days/dates/remove");
        delete msg.language;
        msg.date_id = record.id;
        await this._hass.callWS(msg);
        this._returnFocus = "add"; // the row is gone
        dialog.dismiss(true);
        await this._load();
        this._toast(this._t("deleted"));
      } catch (err) {
        ok.disabled = false;
        this._toast(this._t("save_error"));
      }
    });
    this._showDialog(dialog, opener, cancel);
  }

  _showDialog(dialog, opener, initialFocus) {
    this.shadowRoot.appendChild(dialog);
    const key = opener && opener.getAttribute("data-focus-key");
    // Explicit close (buttons, Escape); the native close event is only a fallback.
    dialog.dismiss = (done) => {
      if (!dialog.isConnected) return;
      // Save / delete choose where focus goes themselves.
      if (!done) this._returnFocus = key;
      if (dialog.open) dialog.close();
      dialog.remove();
      this._render();
    };
    dialog.addEventListener("keydown", (ev) => {
      if (ev.key === "Escape") {
        ev.preventDefault();
        dialog.dismiss(false);
      }
    });
    dialog.addEventListener("close", () => dialog.dismiss(false));
    dialog.showModal();
    if (initialFocus) initialFocus.focus();
  }

  // Add / edit --------------------------------------------------------------

  _openEditor(record, opener) {
    const editing = !!record;
    const state = {
      mode: "hebrew",
      name: editing ? record.name : "",
      kind: editing ? record.kind : "birthday",
      hebrew_day: editing ? String(record.hebrew_day) : "1",
      hebrew_month: editing ? record.hebrew_month : "tishrei",
      original_year: editing && record.original_year ? String(record.original_year) : "",
      gregorian_date: "",
      after_sunset: false,
      adar_rule: editing ? record.adar_rule || "" : "",
      day30_rule: editing ? record.day30_rule || "" : "",
      notes: editing ? record.notes || "" : "",
      reminder_days: new Set(editing ? record.reminder_days || [] : [1]),
      converted: null,
    };
    const errors = {};
    const dialog = mk("dialog");
    dialog.setAttribute("aria-labelledby", "editor-title");
    const form = mk("form");
    form.noValidate = true; // our own inline messages, same rules as the server
    dialog.appendChild(form);

    const fieldIds = {};
    const errorEls = {};
    const inputs = {};

    const field = (key, labelText, control, hint) => {
      const wrap = mk("div", `field ${key}`);
      const id = `f-${key}`;
      control.id = id;
      const label = mk("label", null, labelText);
      label.htmlFor = id;
      const err = mk("span", "err");
      err.id = `${id}-err`;
      err.setAttribute("aria-live", "polite");
      const described = [err.id];
      wrap.append(label, control);
      if (hint) {
        const h = mk("span", "hint", hint);
        h.id = `${id}-hint`;
        described.push(h.id);
        wrap.appendChild(h);
      }
      wrap.appendChild(err);
      control.setAttribute("aria-describedby", described.join(" "));
      fieldIds[key] = id;
      errorEls[key] = err;
      inputs[key] = control;
      return wrap;
    };

    const select = (options, value) => {
      const s = mk("select");
      options.forEach(([v, text]) => s.appendChild(new Option(text, v)));
      s.value = value;
      return s;
    };

    const title = mk("h2", null, this._t(editing ? "dialog_edit" : "dialog_add"));
    title.id = "editor-title";
    form.appendChild(title);

    const name = mk("input");
    name.type = "text";
    name.maxLength = MAX_NAME;
    name.required = true;
    name.autocomplete = "off";
    name.value = state.name;
    name.addEventListener("input", () => { state.name = name.value; clearError("name"); });
    form.appendChild(field("name", this._t("name"), name));

    const kind = select(KINDS.map((k) => [k, this._t(`k_${k}`)]), state.kind);
    kind.addEventListener("change", () => { state.kind = kind.value; refreshRules(); refreshReminderLabels(); });
    form.appendChild(field("kind", this._t("kind"), kind));

    const modes = mk("fieldset");
    modes.appendChild(mk("legend", null, this._t("date_mode")));
    ["hebrew", "gregorian"].forEach((m) => {
      const label = mk("label");
      const radio = mk("input");
      radio.type = "radio";
      radio.name = "mode";
      radio.value = m;
      radio.checked = state.mode === m;
      radio.addEventListener("change", () => { state.mode = m; refreshMode(); });
      label.append(radio, mk("span", null, this._t(`mode_${m}`)));
      modes.appendChild(label);
    });
    form.appendChild(modes);

    // Hebrew date inputs
    const hebrewBox = mk("div", "row3");
    const day = select(Array.from({ length: 30 }, (_, i) => [String(i + 1), langOf(this._hass) === "he" ? `${gematriaDay(i + 1)} (${i + 1})` : String(i + 1)]), state.hebrew_day);
    day.addEventListener("change", () => { state.hebrew_day = day.value; clearError("hebrew_day"); refreshRules(); });
    const month = select(MONTHS.map((m) => [m, this._monthLabel(m, true)]), state.hebrew_month);
    month.addEventListener("change", () => { state.hebrew_month = month.value; clearError("hebrew_day"); refreshRules(); });
    // Text, not number: people copy the year in letters (תש״ע) from a stone or a card. Both forms are parsed.
    const year = mk("input");
    year.type = "text";
    year.autocomplete = "off";
    year.maxLength = 12;
    year.value = state.original_year;
    const yearEcho = mk("span", "year-echo");
    yearEcho.id = "f-original_year-echo";
    const echoYear = () => {
      const text = year.value.trim();
      const parsed = parseHebrewYear(text);
      yearEcho.textContent = "";
      if (!text || parsed == null || parsed < 3000 || parsed > 6500) return;
      yearEcho.textContent = this._t("year_parsed", /^\d+$/.test(text) ? gematriaYear(parsed) : String(parsed));
    };
    year.addEventListener("input", () => { state.original_year = year.value.trim(); clearError("original_year"); echoYear(); });
    hebrewBox.append(
      field("hebrew_day", this._t("day"), day),
      field("hebrew_month", this._t("month"), month),
      field("original_year", this._t("year"), year, this._t("year_hint")),
    );
    const yearField = hebrewBox.querySelector(".field.original_year");
    yearField.classList.add("year");
    yearField.insertBefore(yearEcho, year.nextSibling);
    year.setAttribute("aria-describedby", `${yearEcho.id} ${year.getAttribute("aria-describedby")}`);
    echoYear();
    form.appendChild(hebrewBox);

    // Gregorian date inputs
    const gregBox = mk("div", "field");
    const greg = mk("input");
    greg.type = "date";
    greg.addEventListener("change", () => { state.gregorian_date = greg.value; clearError("gregorian_date"); convert(); });
    const sunsetLabel = mk("label", "check");
    const sunset = mk("input");
    sunset.type = "checkbox";
    sunset.addEventListener("change", () => { state.after_sunset = sunset.checked; convert(); });
    sunsetLabel.append(sunset, mk("span", null, this._t("after_sunset")));
    const convertedEl = mk("span", "hint");
    convertedEl.setAttribute("aria-live", "polite");
    gregBox.append(field("gregorian_date", this._t("gregorian_date"), greg), sunsetLabel, convertedEl);
    form.appendChild(gregBox);

    // Rules
    const adar = select([], "");
    adar.addEventListener("change", () => { state.adar_rule = adar.value; });
    const adarField = field("adar_rule", this._t("adar_rule"), adar);
    form.appendChild(adarField);
    const day30 = select([["", "—"], ["next", this._t("d_next")], ["29", this._t("d_29")]], state.day30_rule);
    day30.options[0].textContent = this._t("adar_default", this._t("d_next"));
    day30.addEventListener("change", () => { state.day30_rule = day30.value; });
    const day30Field = field("day30_rule", this._t("day30_rule"), day30);
    form.appendChild(day30Field);

    const reminders = mk("fieldset");
    reminders.appendChild(mk("legend", null, this._t("remind")));
    const reminderLabels = [];
    [...new Set([0, 1, 3, 7, ...state.reminder_days])].sort((a, b) => a - b).forEach((n) => {
      const label = mk("label");
      const box = mk("input");
      box.type = "checkbox";
      box.checked = state.reminder_days.has(n);
      box.addEventListener("change", () => {
        if (box.checked) state.reminder_days.add(n); else state.reminder_days.delete(n);
      });
      const text = mk("span");
      reminderLabels.push([n, text]);
      label.append(box, text);
      reminders.appendChild(label);
    });
    const remindHint = mk("span", "hint", this._t("remind_hint"));
    form.append(reminders, remindHint);
    const refreshReminderLabels = () => reminderLabels.forEach(([n, text]) => {
      text.textContent = n === 0
        ? this._t(state.kind === "yahrzeit" ? "r_0_yahrzeit" : "r_0")
        : n === 1 ? this._t("r_1") : this._t("r_n", n);
    });
    refreshReminderLabels();

    const notes = mk("textarea");
    notes.rows = 2;
    notes.maxLength = MAX_NOTES;
    notes.value = state.notes;
    notes.addEventListener("input", () => { state.notes = notes.value; clearError("notes"); });
    form.appendChild(field("notes", this._t("notes"), notes));

    const formError = mk("p", "err");
    formError.setAttribute("role", "alert");
    form.appendChild(formError);

    const buttons = mk("div", "buttons");
    const cancel = mk("button", "text", this._t("cancel"));
    cancel.type = "button";
    cancel.addEventListener("click", () => dialog.dismiss(false));
    const save = mk("button", "primary", this._t("save"));
    save.type = "submit";
    buttons.append(cancel, save);
    form.appendChild(buttons);

    const effectiveMonth = () => (state.mode === "gregorian" && state.converted ? state.converted.hebrew_month : state.hebrew_month);
    const effectiveDay = () => (state.mode === "gregorian" && state.converted ? String(state.converted.hebrew_day) : state.hebrew_day);

    const refreshRules = () => {
      const m = effectiveMonth();
      const defaultMonth = state.kind === "yahrzeit" ? "adar_i" : "adar_ii";
      adar.textContent = "";
      [["", this._t("adar_default", this._t(`a_${defaultMonth}`))], ["adar_i", this._t("a_adar_i")], ["adar_ii", this._t("a_adar_ii")], ["both", this._t("a_both")]]
        .forEach(([v, text]) => adar.appendChild(new Option(text, v)));
      adar.value = state.adar_rule;
      adarField.hidden = m !== "adar";
      day30Field.hidden = !(effectiveDay() === "30" && DAY30_MONTHS.has(m));
    };
    const refreshMode = () => {
      hebrewBox.hidden = state.mode !== "hebrew";
      gregBox.hidden = state.mode !== "gregorian";
      refreshRules();
    };
    let convertSeq = 0;
    const convert = async () => {
      const seq = ++convertSeq;
      state.converted = null;
      convertedEl.textContent = "";
      if (!state.gregorian_date) { refreshRules(); return; }
      try {
        const res = await this._hass.callWS({ type: "good_days/dates/convert", date: state.gregorian_date, after_sunset: state.after_sunset });
        if (seq !== convertSeq) return; // a newer date / sunset choice is in flight
        if (res.errors && Object.keys(res.errors).length) {
          showErrors(res.errors);
        } else {
          state.converted = res;
          convertedEl.textContent = this._t("converted", res.display[langOf(this._hass)]);
        }
      } catch (err) {
        if (seq !== convertSeq) return;
        showErrors({ gregorian_date: "invalid_date" });
      }
      refreshRules();
    };

    const clearError = (key) => {
      delete errors[key];
      if (errorEls[key]) errorEls[key].textContent = "";
      if (inputs[key]) inputs[key].removeAttribute("aria-invalid");
    };
    const showErrors = (errs) => {
      Object.keys(errorEls).forEach(clearError);
      formError.textContent = "";
      let first = null;
      Object.entries(errs).forEach(([key, code]) => {
        errors[key] = code;
        const text = this._t(`e_${code}`) || code;
        if (errorEls[key]) {
          errorEls[key].textContent = text;
          inputs[key].setAttribute("aria-invalid", "true");
          if (!first && !inputs[key].closest("[hidden]")) first = inputs[key];
        } else {
          formError.textContent = text;
        }
      });
      if (first) first.focus();
    };

    // Same rules as storage.validate_date on the server.
    const validate = () => {
      const errs = {};
      const n = state.name.trim();
      if (!n || n.length > MAX_NAME) errs.name = "invalid_name";
      if (state.mode === "hebrew") {
        const d = Number(state.hebrew_day);
        if (!Number.isInteger(d) || d < 1 || d > 30 || (d === 30 && MONTHS_29.has(state.hebrew_month))) errs.hebrew_day = "invalid_day";
        if (state.original_year !== "") {
          const y = parseHebrewYear(state.original_year);
          if (!Number.isInteger(y) || y < 3000 || y > 6500) errs.original_year = "invalid_year";
        }
      } else if (!state.gregorian_date || !state.converted) {
        errs.gregorian_date = "invalid_date";
      }
      if (state.notes.length > MAX_NOTES) errs.notes = "invalid_notes";
      return errs;
    };

    form.addEventListener("submit", async (ev) => {
      ev.preventDefault();
      const errs = validate();
      if (Object.keys(errs).length) { showErrors(errs); return; }
      const msg = this._baseMsg(editing ? "good_days/dates/update" : "good_days/dates/add");
      if (editing) msg.date_id = record.id;
      Object.assign(msg, {
        name: state.name.trim(),
        kind: state.kind,
        adar_rule: state.adar_rule || null,
        day30_rule: state.day30_rule || null,
        notes: state.notes.trim(),
        reminder_days: [...state.reminder_days].sort((a, b) => a - b),
      });
      if (state.mode === "hebrew") {
        Object.assign(msg, {
          hebrew_day: Number(state.hebrew_day),
          hebrew_month: state.hebrew_month,
          original_year: state.original_year === "" ? null : parseHebrewYear(state.original_year),
        });
      } else {
        Object.assign(msg, { gregorian_date: state.gregorian_date, after_sunset: state.after_sunset });
      }
      save.disabled = true;
      try {
        const result = await this._hass.callWS(msg);
        if (result.errors && Object.keys(result.errors).length) {
          showErrors(result.errors);
          save.disabled = false;
          return;
        }
        this._returnFocus = opener ? opener.getAttribute("data-focus-key") : "add";
        if (!this.shadowRoot.querySelector(`[data-focus-key="${CSS.escape(this._returnFocus)}"]`)) this._returnFocus = "add";
        dialog.dismiss(true);
        await this._load();
        this._toast(this._t("saved"));
      } catch (err) {
        save.disabled = false;
        formError.textContent = this._t("save_error");
      }
    });

    refreshMode();
    this._showDialog(dialog, opener, name);
  }
  // Shabbat timers tab ------------------------------------------------------

  async _loadTimers() {
    const msg = { type: "good_days/timers/get", language: langOf(this._hass) };
    if (this._entryId) msg.entry_id = this._entryId;
    // Preview the profile being viewed (a dry run; the active profile is not changed).
    if (this._shownProfile) msg.profile = this._shownProfile;
    try {
      this._timers = await this._hass.callWS(msg);
    } catch (err) {
      this._timers = null;
    }
  }

  async _timersCall(msg) {
    const full = { language: langOf(this._hass), ...msg };
    if (this._entryId) full.entry_id = this._entryId;
    return this._hass.callWS(full);
  }

  async _timerSettings(patch) {
    try {
      const view = await this._timersCall({ type: "good_days/timers/settings", ...patch });
      this._timers = view;
      if (view.errors && Object.keys(view.errors).length) this._toast(this._t("save_error"));
      // The reply previews the active profile; fetch the preview of the one being viewed.
      else if (this._viewedProfile() !== view.active_profile) await this._loadTimers();
    } catch (err) {
      this._toast(this._t("save_error"));
    }
    this._render();
  }

  _renderTabs(root) {
    const tabs = mk("div", "tabs");
    tabs.setAttribute("role", "tablist");
    tabs.setAttribute("aria-label", this._t("title"));
    const names = ["dates", "timers"];
    names.forEach((name) => {
      const tab = mk("button", "tab", this._t(`tab_${name}`));
      tab.type = "button";
      tab.id = `tab-${name}`;
      tab.setAttribute("role", "tab");
      tab.setAttribute("aria-selected", String(this._tab === name));
      tab.setAttribute("aria-controls", `panel-${name}`);
      tab.tabIndex = this._tab === name ? 0 : -1;
      tab.setAttribute("data-focus-key", `tab-${name}`);
      tab.addEventListener("click", () => this._selectTab(name));
      tab.addEventListener("keydown", (ev) => {
        const i = names.indexOf(name);
        const rtl = langOf(this._hass) === "he";
        let next = null;
        if (ev.key === (rtl ? "ArrowLeft" : "ArrowRight")) next = names[(i + 1) % names.length];
        if (ev.key === (rtl ? "ArrowRight" : "ArrowLeft")) next = names[(i - 1 + names.length) % names.length];
        if (ev.key === "Home") next = names[0];
        if (ev.key === "End") next = names[names.length - 1];
        if (next) {
          ev.preventDefault();
          this._selectTab(next, true);
        }
      });
      tabs.appendChild(tab);
    });
    root.appendChild(tabs);
  }

  _selectTab(name, focus = false) {
    this._tab = name;
    try { localStorage.setItem("good_days_tab", name); } catch (err) { /* private mode */ }
    if (focus) this._returnFocus = `tab-${name}`;
    this._render();
  }

  _friendly(entityId) {
    const state = this._hass.states && this._hass.states[entityId];
    return (state && state.attributes && state.attributes.friendly_name) || entityId;
  }

  _when(value, withDay = true) {
    const date = new Date(value);
    const locale = langOf(this._hass) === "he" ? "he-IL" : (this._hass.locale && this._hass.locale.language) || "en";
    const time = date.toLocaleTimeString(locale, { hour: "2-digit", minute: "2-digit", hourCycle: "h23" });
    if (!withDay) return iso(time);
    return `${date.toLocaleDateString(locale, { weekday: "short" })} ${iso(time)}`;
  }

  _ruleSummary(rule) {
    const parts = [this._t(`act_${rule.action}`)];
    if (rule.anchor === "clock") {
      parts.push(`${iso(rule.time)} · ${this._t(`days_${rule.days}`)}`);
    } else {
      const minutes = Math.abs(rule.offset_min || 0);
      const side = (rule.offset_min || 0) < 0 ? "before" : "after";
      parts.push(minutes === 0 ? this._t(`at_${rule.anchor}`) : this._t(`${side}_${rule.anchor}`, minutes));
    }
    parts.push(rule.applies_to.map((k) => this._t(`kind_${k}`)).join(", "));
    return parts.join(" · ");
  }

  _renderTimers(main) {
    const view = this._timers;
    if (!view) {
      main.appendChild(mk("p", "status error", this._t("load_error")));
      return;
    }
    const admin = this._isAdmin();
    if (!admin) {
      const notice = mk("p", "notice", this._t("readonly_notice"));
      notice.id = "timers-readonly";
      main.appendChild(notice);
    }
    const viewed = this._viewedProfile();

    // Status
    const status = mk("section", "card timers-status");
    status.setAttribute("aria-label", this._t("timers_status"));
    const toggle = (key, checked, text, onChange) => {
      const label = mk("label", "check");
      const box = mk("input");
      box.type = "checkbox";
      box.setAttribute("role", "switch");
      box.checked = checked;
      box.disabled = !admin;
      if (!admin) box.setAttribute("aria-describedby", "timers-readonly");
      box.setAttribute("data-focus-key", key);
      box.addEventListener("change", () => onChange(box.checked));
      label.append(box, mk("span", null, text));
      return label;
    };
    status.appendChild(toggle("timers-enabled", view.enabled, this._t("timers_enabled"), (on) => this._timerSettings({ enabled: on })));
    const nextPeriod = view.preview[0];
    if (nextPeriod) {
      const skip = toggle("timers-skip", view.skip_next, this._t("timers_skip", nextPeriod.title), (on) => this._timerSettings({ skip_next: on }));
      const skipHint = mk("span", "hint", this._t("skip_hint"));
      skipHint.id = "timers-skip-hint";
      const box = skip.querySelector("input");
      box.setAttribute("aria-describedby", [skipHint.id, admin ? null : "timers-readonly"].filter(Boolean).join(" "));
      status.append(skip, skipHint);
    }
    const profileRow = mk("div", "row-inline");
    const profileLabel = mk("label", null, this._t("profile_active"));
    profileLabel.htmlFor = "timers-profile";
    const profile = mk("select");
    profile.id = "timers-profile";
    profile.disabled = !admin;
    if (!admin) profile.setAttribute("aria-describedby", "timers-readonly");
    profile.setAttribute("data-focus-key", "timers-profile");
    view.profiles.forEach((p) => profile.appendChild(new Option(this._profileName(p), p)));
    profile.value = view.active_profile;
    profile.addEventListener("change", () => this._timerSettings({ active_profile: profile.value }));
    profileRow.append(profileLabel, profile);
    if (admin) {
      const manage = mk("button", "text", this._t("profiles_manage"));
      manage.type = "button";
      manage.setAttribute("data-focus-key", "profiles-manage");
      manage.addEventListener("click", () => this._openProfiles(manage));
      profileRow.appendChild(manage);
    }
    status.appendChild(profileRow);
    const next = view.next_action;
    let nextText = this._t("no_next_action");
    if (next) {
      const act = this._t(`act_${next.action}`);
      // Preset names already say on / off ("Hot plate (on)").
      nextText = next.rule_name.toLowerCase().includes(`(${act.toLowerCase()})`)
        ? this._t("next_action_named", this._when(next.when), next.rule_name)
        : this._t("next_action", this._when(next.when), next.rule_name, act);
    }
    status.appendChild(mk("p", "hint", nextText));
    main.appendChild(status);

    // Preview (dry run of the next Shabbat / Chag)
    view.preview.forEach((period, index) => {
      const card = mk("section", "card preview");
      const headingId = `preview-${index}`;
      card.setAttribute("aria-labelledby", headingId);
      const h = mk("h2", null, `${period.title} · ${this._when(period.start)} – ${this._when(period.end)}`);
      h.id = headingId;
      card.appendChild(h);
      if (viewed !== view.active_profile) card.appendChild(mk("p", "warn", this._t("preview_not_active", this._profileName(viewed))));
      else if (view.profiles.length > 1) card.appendChild(mk("p", "hint", this._t("preview_profile", this._profileName(viewed))));
      if (period.skipped) card.appendChild(mk("p", "warn", this._t("period_skipped")));
      if (!period.actions.length) {
        card.appendChild(mk("p", "hint", this._t("no_actions")));
      } else {
        const list = mk("ol", "timeline");
        period.actions.forEach((a) => {
          const li = mk("li", period.skipped ? "skipped" : a.done ? "done" : null);
          li.appendChild(mk("span", "time", this._when(a.when)));
          // Skipped: the row says so instead of showing an on / off chip that will not happen.
          li.appendChild(period.skipped
            ? mk("span", "act skip", this._t("wont_run"))
            : mk("span", `act ${a.action}`, this._t(`act_${a.action}`)));
          const what = mk("span", "what", `${a.rule_name}: ${a.targets.map((t) => this._friendly(t)).join(", ")}`);
          li.appendChild(what);
          if (a.outside) li.appendChild(mk("span", "badge-soft", this._t(new Date(a.when) < new Date(period.start) ? "before_period" : "after_period")));
          if (a.done) li.appendChild(mk("span", "badge-soft", this._t("done")));
          list.appendChild(li);
        });
        card.appendChild(list);
      }
      period.conflicts.forEach((c) => {
        card.appendChild(mk("p", "warn", this._t("conflict", this._friendly(c.target), this._when(c.when))));
      });
      main.appendChild(card);
    });

    // Rules
    const rulesCard = mk("section", "card rules");
    rulesCard.setAttribute("aria-labelledby", "rules-title");
    const head = mk("div", "rules-head");
    const title = mk("h2", null, this._t("rules_title", this._profileName(viewed)));
    title.id = "rules-title";
    head.appendChild(title);
    if (admin) {
      const add = mk("button", "primary", this._t("timer_add"));
      add.type = "button";
      add.setAttribute("data-focus-key", "timer-add");
      add.addEventListener("click", () => this._openTimerEditor(null, add));
      const preset = mk("button", "text", this._t("timer_preset"));
      preset.type = "button";
      preset.setAttribute("data-focus-key", "timer-preset");
      preset.addEventListener("click", () => this._openPreset(preset));
      head.append(preset, add);
    }
    rulesCard.appendChild(head);
    // Which profile is shown and edited here, separate from the active one (which decides what runs).
    if (view.profiles.length > 1) {
      const group = mk("div", "profile-view");
      group.setAttribute("role", "group");
      const groupLabel = mk("span", "label", this._t(admin ? "profile_view" : "profile_view_ro"));
      groupLabel.id = "profile-view-label";
      group.setAttribute("aria-labelledby", "profile-view-label");
      group.appendChild(groupLabel);
      view.profiles.forEach((p) => {
        const name = this._profileName(p);
        const b = mk("button", null, p === view.active_profile ? `${name} · ${this._t("profile_is_active")}` : name);
        b.type = "button";
        b.setAttribute("aria-pressed", String(p === viewed));
        b.setAttribute("data-focus-key", `view-profile-${p}`);
        b.addEventListener("click", () => this._viewProfile(p));
        group.appendChild(b);
      });
      rulesCard.appendChild(group);
    }
    const rules = view.rules.filter((r) => r.profile === viewed);
    if (!rules.length) {
      rulesCard.appendChild(mk("p", "empty", this._t("rules_empty")));
    } else {
      const list = mk("ul", "dates");
      list.setAttribute("aria-labelledby", "rules-title");
      rules.forEach((rule) => list.appendChild(this._renderRuleRow(rule, admin)));
      rulesCard.appendChild(list);
    }
    main.appendChild(rulesCard);

    // History
    if (view.history.length) {
      const details = mk("details", "card history");
      details.appendChild(mk("summary", null, this._t("history")));
      const list = mk("ul", "history-list");
      view.history.forEach((h) => {
        const text = `${this._when(h.when)} · ${h.rule_name} · ${this._t(`act_${h.action}`)} · ${this._t(`st_${h.status}`)}${h.reason ? ` (${h.reason})` : ""}`;
        list.appendChild(mk("li", `st-${h.status}`, text));
      });
      details.appendChild(list);
      main.appendChild(details);
    }
  }

  _profileName(p) {
    return p === "default" ? this._t("profile_default") : p;
  }

  // The profile shown and edited in the timers tab; the active one unless the user picked another.
  _viewedProfile() {
    const view = this._timers;
    if (!view) return null;
    return this._shownProfile && view.profiles.includes(this._shownProfile) ? this._shownProfile : view.active_profile;
  }

  async _viewProfile(p) {
    this._shownProfile = p;
    this._returnFocus = `view-profile-${p}`;
    await this._loadTimers();
    this._render();
  }

  _renderRuleRow(rule, admin) {
    const li = mk("li", rule.enabled ? null : "disabled");
    const icon = document.createElement("ha-icon");
    icon.className = "kind";
    icon.setAttribute("icon", rule.action === "on" ? "mdi:power" : "mdi:power-off");
    icon.setAttribute("aria-hidden", "true");
    li.appendChild(icon);
    const info = mk("div", "info");
    info.appendChild(mk("span", "name", rule.enabled ? rule.name : `${rule.name} (${this._t("disabled")})`));
    const sub = mk("span", "sub");
    sub.appendChild(mk("span", null, this._ruleSummary(rule)));
    sub.appendChild(mk("span", null, rule.targets.map((t) => this._friendly(t)).join(", ")));
    if (rule.conditions && rule.conditions.length) sub.appendChild(mk("span", null, this._t("has_conditions", rule.conditions.length)));
    info.appendChild(sub);
    li.appendChild(info);
    if (!admin) return li;
    const actions = mk("div", "row-actions");
    const button = (key, text, label, cls, handler) => {
      const b = mk("button", cls, text);
      b.type = "button";
      b.setAttribute("aria-label", label);
      b.setAttribute("data-focus-key", `${key}-${rule.id}`);
      b.addEventListener("click", () => handler(b));
      actions.appendChild(b);
    };
    // Name the effect ("turn off now"), not the mechanism: "run" reads as "switch on" in Hebrew.
    const runVerb = this._t(rule.action === "off" ? "run_now_off" : "run_now_on");
    const runTargets = rule.targets.map((t) => this._friendly(t)).join(", ");
    button("run", runVerb, this._t("run_now_named", runVerb, rule.name, runTargets), "text", async () => {
      const res = await this._timersCall({ type: "good_days/timers/run", rule_id: rule.id }).catch(() => ({ errors: { base: 1 } }));
      this._toast(res.errors && Object.keys(res.errors).length ? this._t("run_failed") : this._t("ran"));
    });
    button("dup", this._t("duplicate"), this._t("duplicate_named", rule.name), "text", async () => {
      const res = await this._timersCall({ type: "good_days/timers/duplicate", rule_id: rule.id }).catch(() => ({ errors: { base: 1 } }));
      if (res && res.errors && Object.keys(res.errors).length) {
        this._toast(this._t("save_error"));
        return;
      }
      await this._loadTimers();
      this._render();
    });
    button("edit", this._t("edit"), this._t("edit_named", rule.name), "text", (b) => this._openTimerEditor(rule, b));
    button("del", this._t("delete"), this._t("delete_named", rule.name), "text danger", (b) => this._confirmRemoveRule(rule, b));
    li.appendChild(actions);
    return li;
  }

  _confirmRemoveRule(rule, opener) {
    const dialog = mk("dialog");
    dialog.setAttribute("aria-labelledby", "confirm-title");
    const form = mk("form");
    const title = mk("h2", null, this._t("confirm_delete", rule.name));
    title.id = "confirm-title";
    const formError = mk("p", "err");
    formError.setAttribute("role", "alert");
    const buttons = mk("div", "buttons");
    const cancel = mk("button", "text", this._t("cancel"));
    cancel.type = "button";
    cancel.addEventListener("click", () => dialog.dismiss(false));
    const ok = mk("button", "primary", this._t("delete"));
    ok.type = "submit";
    buttons.append(cancel, ok);
    form.append(title, formError, buttons);
    dialog.appendChild(form);
    form.addEventListener("submit", async (ev) => {
      ev.preventDefault();
      ok.disabled = true;
      formError.textContent = "";
      const res = await this._timersCall({ type: "good_days/timers/remove", rule_id: rule.id }).catch(() => ({ errors: { base: 1 } }));
      if (res && res.errors && Object.keys(res.errors).length) {
        ok.disabled = false;
        formError.textContent = this._t("save_error");
        this._toast(this._t("save_error"));
        return;
      }
      await this._loadTimers();
      this._returnFocus = "timer-add";
      dialog.dismiss(true);
      this._toast(this._t("deleted"));
    });
    this._showDialog(dialog, opener, cancel);
  }

  // A labelled control with an inline error, like the family-date editor.
  _field(form, fields, key, labelText, control, hint) {
    const wrap = mk("div", `field ${key}`);
    const id = `t-${key}`;
    control.id = id;
    const label = mk("label", null, labelText);
    label.htmlFor = id;
    const err = mk("span", "err");
    err.id = `${id}-err`;
    err.setAttribute("aria-live", "polite");
    const described = [err.id];
    wrap.append(label, control);
    if (hint) {
      const h = mk("span", "hint", hint);
      h.id = `${id}-hint`;
      described.push(h.id);
      wrap.appendChild(h);
    }
    wrap.appendChild(err);
    control.setAttribute("aria-describedby", described.join(" "));
    fields[key] = { control, err };
    form.appendChild(wrap);
    if (control.localName === "ha-selector") this._wireSelector(control, labelText, [...described].reverse());
    return wrap;
  }

  // Home Assistant's selectors render their focusable control deep in shadow trees, where <label for> and
  // aria-describedby cannot reach, and HA offers no property that names it. Put our label, hint, error and
  // invalid state on that inner control directly (element references cross shadow boundaries).
  _wireSelector(picker, labelText, describedIds) {
    const apply = () => {
      const inner = deepFocusable(picker);
      if (!inner) return null;
      inner.setAttribute("aria-label", labelText);
      if ("ariaDescribedByElements" in inner) {
        inner.ariaDescribedByElements = describedIds.map((id) => this.shadowRoot.getElementById(id)).filter(Boolean);
      }
      if (picker.getAttribute("aria-invalid") === "true") inner.setAttribute("aria-invalid", "true");
      else inner.removeAttribute("aria-invalid");
      return inner;
    };
    picker.wireInner = apply;
    picker.focusTarget = () => apply() || picker;
    picker.addEventListener("focusin", apply);
    picker.addEventListener("value-changed", () => setTimeout(apply, 0));
    // The nested components render asynchronously after the dialog opens.
    [0, 100, 400, 1000].forEach((ms) => setTimeout(apply, ms));
  }

  _showFieldErrors(fields, formError, errs) {
    Object.values(fields).forEach(({ control, err }) => {
      err.textContent = "";
      control.removeAttribute("aria-invalid");
      if (control.wireInner) control.wireInner();
    });
    formError.textContent = "";
    let first = null;
    Object.entries(errs).forEach(([key, code]) => {
      const text = this._t(`e_${code}`) || code;
      const f = fields[key];
      if (f && !f.control.closest("[hidden]")) {
        f.err.textContent = text;
        f.control.setAttribute("aria-invalid", "true");
        if (f.control.wireInner) f.control.wireInner();
        if (!first) first = f.control.focusTarget ? f.control.focusTarget() : f.control;
      } else {
        formError.textContent = text;
      }
    });
    if (first) first.focus();
  }

  _targetsControl(value) {
    // Home Assistant's own entity picker; falls back to a text field (comma separated).
    if (customElements.get("ha-selector")) {
      const picker = document.createElement("ha-selector");
      picker.hass = this._hass;
      picker.selector = { entity: { multiple: true, filter: [{ domain: TIMER_DOMAINS }] } };
      picker.value = value;
      picker.required = true;
      picker.addEventListener("value-changed", (ev) => { picker.value = ev.detail.value; });
      picker.getValue = () => picker.value || [];
      return picker;
    }
    const input = mk("input");
    input.type = "text";
    input.dir = "ltr";
    input.value = (value || []).join(", ");
    input.getValue = () => input.value.split(",").map((s) => s.trim()).filter(Boolean);
    return input;
  }

  _openTimerEditor(rule, opener) {
    const view = this._timers;
    const editing = !!rule;
    const r = rule || { name: "", targets: [], action: "on", anchor: "candle_lighting", offset_min: -20, time: "23:00",
      days: "each", applies_to: ["shabbat", "yom_tov"], profile: this._viewedProfile(), conditions: [], enabled: true };
    const dialog = mk("dialog");
    dialog.setAttribute("aria-labelledby", "timer-title");
    const form = mk("form");
    form.noValidate = true;
    dialog.appendChild(form);
    const title = mk("h2", null, this._t(editing ? "timer_edit" : "timer_add"));
    title.id = "timer-title";
    form.appendChild(title);
    const fields = {};
    const select = (options, value) => {
      const s = mk("select");
      options.forEach(([v, text]) => s.appendChild(new Option(text, v)));
      s.value = value;
      return s;
    };

    const name = mk("input");
    name.type = "text";
    name.maxLength = MAX_NAME;
    name.value = r.name;
    this._field(form, fields, "name", this._t("name"), name);

    const targets = this._targetsControl(r.targets);
    this._field(form, fields, "targets", this._t("targets"), targets, this._t("targets_hint"));

    const action = select([["on", this._t("act_on")], ["off", this._t("act_off")]], r.action);
    this._field(form, fields, "action", this._t("action"), action);

    const anchor = select(["candle_lighting", "havdalah", "clock"].map((a) => [a, this._t(`anchor_${a}`)]), r.anchor);
    this._field(form, fields, "anchor", this._t("anchor"), anchor);

    const offsetRow = mk("div", "row3");
    const minutes = mk("input");
    minutes.type = "number";
    minutes.min = "0";
    minutes.max = "720";
    minutes.step = "1";
    minutes.inputMode = "numeric";
    minutes.value = String(Math.abs(r.offset_min || 0));
    const side = select([["before", this._t("side_before")], ["after", this._t("side_after")]], (r.offset_min || 0) < 0 ? "before" : "after");
    form.appendChild(offsetRow);
    this._field(offsetRow, fields, "offset_min", this._t("minutes"), minutes);
    this._field(offsetRow, fields, "side", this._t("side"), side);

    const clockRow = mk("div", "row3");
    const time = mk("input");
    time.type = "time";
    time.value = r.time || "23:00";
    const days = select(["each", "first", "last", "erev"].map((d) => [d, this._t(`days_${d}`)]), r.days || "each");
    form.appendChild(clockRow);
    this._field(clockRow, fields, "time", this._t("time"), time, this._t("time_hint"));
    this._field(clockRow, fields, "days", this._t("days"), days);

    const applies = mk("fieldset");
    applies.appendChild(mk("legend", null, this._t("applies_to")));
    const appliesBoxes = {};
    ["shabbat", "yom_tov", "yom_kippur"].forEach((k) => {
      const label = mk("label");
      const box = mk("input");
      box.type = "checkbox";
      box.checked = r.applies_to.includes(k);
      appliesBoxes[k] = box;
      label.append(box, mk("span", null, this._t(`kind_${k}`)));
      applies.appendChild(label);
    });
    const appliesErr = mk("span", "err");
    appliesErr.setAttribute("aria-live", "polite");
    applies.appendChild(appliesErr);
    fields.applies_to = { control: applies, err: appliesErr };
    form.appendChild(applies);

    const profile = select(view.profiles.map((p) => [p, this._profileName(p)]), r.profile);
    this._field(form, fields, "profile", this._t("profile"), profile);

    let conditions = r.conditions || [];
    if (customElements.get("ha-selector")) {
      const cond = document.createElement("ha-selector");
      cond.hass = this._hass;
      cond.selector = { condition: {} };
      cond.value = conditions;
      cond.addEventListener("value-changed", (ev) => { conditions = ev.detail.value || []; cond.value = conditions; });
      this._field(form, fields, "conditions", this._t("conditions"), cond, this._t("conditions_hint"));
    }

    const enabledLabel = mk("label", "check");
    const enabled = mk("input");
    enabled.type = "checkbox";
    enabled.checked = r.enabled !== false;
    enabledLabel.append(enabled, mk("span", null, this._t("enabled")));
    form.appendChild(enabledLabel);

    const formError = mk("p", "err");
    formError.setAttribute("role", "alert");
    form.appendChild(formError);
    const buttons = mk("div", "buttons");
    const cancel = mk("button", "text", this._t("cancel"));
    cancel.type = "button";
    cancel.addEventListener("click", () => dialog.dismiss(false));
    const save = mk("button", "primary", this._t("save"));
    save.type = "submit";
    buttons.append(cancel, save);
    form.appendChild(buttons);

    const refresh = () => {
      offsetRow.hidden = anchor.value === "clock";
      clockRow.hidden = anchor.value !== "clock";
    };
    anchor.addEventListener("change", refresh);
    refresh();

    // Same rules as timers.validate_rule on the server.
    const validate = (data) => {
      const errs = {};
      if (!data.name || data.name.length > MAX_NAME) errs.name = "invalid_name";
      if (!data.targets.length) errs.targets = "invalid_targets";
      if (data.anchor === "clock") {
        if (!/^([01]?\d|2[0-3]):[0-5]\d$/.test(data.time || "")) errs.time = "invalid_time";
      } else {
        const m = Number(minutes.value);
        if (!Number.isInteger(m) || m < 0 || m > 720) errs.offset_min = "invalid_offset";
      }
      if (!data.applies_to.length) errs.applies_to = "invalid_applies_to";
      return errs;
    };

    form.addEventListener("submit", async (ev) => {
      ev.preventDefault();
      const m = Number(minutes.value);
      const data = {
        name: name.value.trim(),
        targets: targets.getValue(),
        action: action.value,
        anchor: anchor.value,
        offset_min: side.value === "before" ? -m : m,
        time: (time.value || "").slice(0, 5),
        days: days.value,
        applies_to: Object.keys(appliesBoxes).filter((k) => appliesBoxes[k].checked),
        profile: profile.value,
        conditions,
        enabled: enabled.checked,
      };
      const errs = validate(data);
      if (Object.keys(errs).length) { this._showFieldErrors(fields, formError, errs); return; }
      save.disabled = true;
      try {
        const res = await this._timersCall({ type: "good_days/timers/save", ...(editing ? { rule_id: rule.id } : {}), ...data });
        if (res.errors && Object.keys(res.errors).length) {
          this._showFieldErrors(fields, formError, res.errors);
          save.disabled = false;
          return;
        }
        await this._loadTimers();
        this._returnFocus = editing ? `edit-${rule.id}` : "timer-add";
        dialog.dismiss(true);
        this._toast(this._t("saved"));
      } catch (err) {
        save.disabled = false;
        formError.textContent = this._t("save_error");
      }
    });
    this._showDialog(dialog, opener, name);
  }

  _openPreset(opener) {
    const view = this._timers;
    const dialog = mk("dialog");
    dialog.setAttribute("aria-labelledby", "preset-title");
    const form = mk("form");
    form.noValidate = true;
    dialog.appendChild(form);
    const title = mk("h2", null, this._t("timer_preset"));
    title.id = "preset-title";
    form.appendChild(title);
    const fields = {};
    const preset = mk("select");
    view.presets.forEach((p) => preset.appendChild(new Option(this._t(`preset_${p}`), p)));
    this._field(form, fields, "preset", this._t("preset"), preset, this._t("preset_hint"));
    const name = mk("input");
    name.type = "text";
    name.maxLength = MAX_NAME - 12;
    name.value = this._t(`preset_${view.presets[0]}`);
    preset.addEventListener("change", () => { name.value = this._t(`preset_${preset.value}`); });
    this._field(form, fields, "name", this._t("name"), name);
    const targets = this._targetsControl([]);
    this._field(form, fields, "targets", this._t("targets"), targets);
    const formError = mk("p", "err");
    formError.setAttribute("role", "alert");
    form.appendChild(formError);
    const buttons = mk("div", "buttons");
    const cancel = mk("button", "text", this._t("cancel"));
    cancel.type = "button";
    cancel.addEventListener("click", () => dialog.dismiss(false));
    const save = mk("button", "primary", this._t("save"));
    save.type = "submit";
    buttons.append(cancel, save);
    form.appendChild(buttons);
    form.addEventListener("submit", async (ev) => {
      ev.preventDefault();
      const data = { preset: preset.value, name: name.value.trim(), targets: targets.getValue(), profile: this._viewedProfile() };
      const errs = {};
      if (!data.name) errs.name = "invalid_name";
      if (!data.targets.length) errs.targets = "invalid_targets";
      if (Object.keys(errs).length) { this._showFieldErrors(fields, formError, errs); return; }
      save.disabled = true;
      try {
        const res = await this._timersCall({ type: "good_days/timers/preset", ...data });
        if (res.errors && Object.keys(res.errors).length) {
          this._showFieldErrors(fields, formError, res.errors);
          save.disabled = false;
          return;
        }
        await this._loadTimers();
        this._returnFocus = "timer-add";
        dialog.dismiss(true);
        this._toast(this._t("saved"));
      } catch (err) {
        save.disabled = false;
        formError.textContent = this._t("save_error");
      }
    });
    this._showDialog(dialog, opener, preset);
  }

  _openProfiles(opener) {
    const view = this._timers;
    const dialog = mk("dialog");
    dialog.setAttribute("aria-labelledby", "profiles-title");
    const form = mk("form");
    form.noValidate = true;
    dialog.appendChild(form);
    const title = mk("h2", null, this._t("profiles_manage"));
    title.id = "profiles-title";
    form.appendChild(title);
    const list = mk("ul", "profile-list");
    view.profiles.forEach((p) => {
      const li = mk("li");
      const count = view.rules.filter((r) => r.profile === p).length;
      const label = mk("span", "name", `${this._profileName(p)} · ${this._t("profile_timers", count)}`);
      li.appendChild(label);
      const rename = mk("button", "text", this._t("rename"));
      rename.type = "button";
      rename.setAttribute("aria-label", this._t("rename_named", this._profileName(p)));
      rename.addEventListener("click", () => {
        // Inline: the name becomes a text field with its own save.
        const box = mk("span", "row-inline");
        const input = mk("input");
        input.type = "text";
        input.maxLength = 40;
        input.value = this._profileName(p);
        input.setAttribute("aria-label", this._t("rename_named", this._profileName(p)));
        const err = mk("span", "err");
        err.id = `rename-err-${view.profiles.indexOf(p)}`;
        err.setAttribute("aria-live", "polite");
        input.setAttribute("aria-describedby", err.id);
        const ok = mk("button", "primary", this._t("save"));
        ok.type = "button";
        ok.addEventListener("click", async () => {
          const value = input.value.trim();
          if (!value || value.length > 40 || (value !== p && view.profiles.includes(value))) {
            err.textContent = this._t("e_invalid_profile_name");
            input.setAttribute("aria-invalid", "true");
            input.focus();
            return;
          }
          if (value === p || (p === "default" && value === this._profileName(p))) { dialog.dismiss(false); return; }
          const res = await this._timersCall({ type: "good_days/timers/settings", rename_profile: p, new_name: value }).catch(() => null);
          if (!res || (res.errors && Object.keys(res.errors).length)) {
            err.textContent = this._t("e_invalid_profile_name");
            input.setAttribute("aria-invalid", "true");
            input.focus();
            return;
          }
          this._timers = res;
          if (this._shownProfile === p) this._shownProfile = value;
          if (this._viewedProfile() !== res.active_profile) await this._loadTimers();
          this._returnFocus = "profiles-manage";
          dialog.dismiss(true);
          this._toast(this._t("saved"));
        });
        input.addEventListener("keydown", (ev) => { if (ev.key === "Enter") { ev.preventDefault(); ok.click(); } });
        box.append(input, ok, err);
        li.replaceChildren(box);
        input.focus();
      });
      const acts = mk("span", "row-actions");
      acts.appendChild(rename);
      if (view.profiles.length > 1) {
        const del = mk("button", "text danger", this._t("delete"));
        del.type = "button";
        del.setAttribute("aria-label", this._t("delete_named", this._profileName(p)));
        del.addEventListener("click", async () => {
          await this._timerSettings({ remove_profile: p });
          dialog.dismiss(true);
        });
        acts.appendChild(del);
      }
      li.appendChild(acts);
      list.appendChild(li);
    });
    form.appendChild(list);
    const fields = {};
    const name = mk("input");
    name.type = "text";
    name.maxLength = 40;
    this._field(form, fields, "add_profile", this._t("profile_new"), name, this._t("profile_new_hint"));
    const copy = mk("select");
    copy.appendChild(new Option(this._t("profile_empty"), ""));
    view.profiles.forEach((p) => copy.appendChild(new Option(this._t("profile_copy", this._profileName(p)), p)));
    this._field(form, fields, "copy_from", this._t("profile_start"), copy);
    const formError = mk("p", "err");
    formError.setAttribute("role", "alert");
    form.appendChild(formError);
    const buttons = mk("div", "buttons");
    const close = mk("button", "text", this._t("close"));
    close.type = "button";
    close.addEventListener("click", () => dialog.dismiss(false));
    const add = mk("button", "primary", this._t("profile_add"));
    add.type = "submit";
    buttons.append(close, add);
    form.appendChild(buttons);
    form.addEventListener("submit", async (ev) => {
      ev.preventDefault();
      const value = name.value.trim();
      if (!value || value.length > 40 || view.profiles.includes(value)) {
        this._showFieldErrors(fields, formError, { add_profile: "invalid_profile_name" });
        return;
      }
      const res = await this._timersCall({ type: "good_days/timers/settings", add_profile: value, ...(copy.value ? { copy_from: copy.value } : {}) }).catch(() => null);
      if (!res || (res.errors && Object.keys(res.errors).length)) {
        this._showFieldErrors(fields, formError, (res && res.errors) || { base: "save_error" });
        return;
      }
      this._timers = res;
      if (this._viewedProfile() !== res.active_profile) await this._loadTimers();
      this._returnFocus = "profiles-manage";
      dialog.dismiss(true);
      this._toast(this._t("saved"));
    });
    this._showDialog(dialog, opener, name);
  }
}

if (!customElements.get("good-days-panel")) {
  customElements.define("good-days-panel", GoodDaysPanel);
}
