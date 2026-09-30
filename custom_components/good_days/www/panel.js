/* Good Days sidebar panel: family dates (birthdays, yahrzeits, anniversaries) by Hebrew date. */

const FSI = "⁨";
const PDI = "⁩";
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

const I18N = {
  en: {
    title: "Family dates",
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
    year_hint: "Shows age or number of years, e.g. 5745.",
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
    e_invalid_year: "Enter a Hebrew year between 3000 and 6500, e.g. 5745.",
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
    title: "תאריכים משפחתיים",
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
    year_hint: "מציג גיל או מספר שנים, למשל 5745.",
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
    e_invalid_year: "יש להזין שנה עברית בין 3000 ל-6500, למשל 5745.",
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

const STYLE = `
  [hidden] { display: none !important; }
  :host { display: block; min-height: 100vh; background: var(--primary-background-color); color: var(--primary-text-color);
    font-family: var(--paper-font-body1_-_font-family, Roboto, sans-serif); }
  .toolbar { display: flex; align-items: center; gap: 8px; height: var(--header-height, 56px); padding: 0 12px;
    background: var(--app-header-background-color, var(--primary-color)); color: var(--app-header-text-color, #fff);
    box-sizing: border-box; }
  .toolbar h1 { flex: 1; font-size: 20px; font-weight: 400; margin: 0; }
  .toolbar select { font: inherit; padding: 4px 8px; border-radius: 6px; }
  main { max-width: 760px; margin: 0 auto; padding: 16px; box-sizing: border-box; }
  .actions { display: flex; justify-content: flex-end; margin-bottom: 12px; }
  button { font: inherit; cursor: pointer; }
  button.primary { background: var(--primary-color); color: var(--text-primary-color, #fff); border: none; border-radius: 8px;
    padding: 8px 16px; display: inline-flex; align-items: center; gap: 6px; }
  button.text { background: none; border: none; color: var(--primary-color); padding: 6px 10px; border-radius: 6px; }
  button.danger { color: var(--error-color, #db4437); }
  button:focus-visible, input:focus-visible, select:focus-visible, textarea:focus-visible {
    outline: 2px solid var(--primary-color); outline-offset: 2px; }
  .card { background: var(--card-background-color); border-radius: 12px; box-shadow: var(--ha-card-box-shadow, 0 1px 3px rgba(0,0,0,.2)); }
  ul.dates { list-style: none; margin: 0; padding: 0; }
  ul.dates li { display: flex; align-items: center; gap: 12px; padding: 12px 16px; border-bottom: 1px solid var(--divider-color); }
  ul.dates li:last-child { border-bottom: none; }
  ha-icon.kind { color: var(--secondary-text-color); flex: none; }
  .info { flex: 1; min-width: 0; display: grid; gap: 2px; }
  .name { font-weight: 500; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
  .sub { font-size: 0.85rem; color: var(--secondary-text-color); display: flex; flex-wrap: wrap; gap: 4px 10px; }
  .chip { font-size: 0.78rem; padding: 2px 8px; border-radius: 999px; background: var(--secondary-background-color); white-space: nowrap; }
  .chip.now { background: var(--primary-color); color: var(--text-primary-color, #fff); }
  .conflict { color: var(--warning-color, #ff9800); }
  .row-actions { display: flex; gap: 2px; flex: none; }
  .card.ics { margin-top: 16px; padding: 16px; display: grid; gap: 10px; }
  .card.ics h2 { margin: 0; font-size: 1.05rem; font-weight: 500; }
  .ics-buttons { display: flex; flex-wrap: wrap; gap: 4px; }
  a.text { color: var(--primary-color); padding: 6px 10px; text-decoration: none; border-radius: 6px; }
  a.text:focus-visible { outline: 2px solid var(--primary-color); outline-offset: 2px; }
  .empty, .status { padding: 24px 16px; color: var(--secondary-text-color); }
  .status.error { color: var(--error-color, #db4437); }
  dialog { border: none; border-radius: 16px; padding: 0; width: min(520px, calc(100vw - 32px)); max-height: calc(100vh - 32px);
    background: var(--card-background-color); color: var(--primary-text-color); box-shadow: 0 8px 32px rgba(0,0,0,.3); }
  dialog::backdrop { background: rgba(0,0,0,.4); }
  form { display: grid; gap: 14px; padding: 20px; }
  form h2 { margin: 0; font-size: 1.2rem; font-weight: 500; }
  .field { display: grid; gap: 4px; }
  .field label, fieldset legend { font-size: 0.85rem; color: var(--secondary-text-color); }
  input, select, textarea { font: inherit; padding: 8px 10px; border-radius: 8px; border: 1px solid var(--divider-color);
    background: var(--card-background-color); color: var(--primary-text-color); box-sizing: border-box; width: 100%; }
  input[type=checkbox], input[type=radio] { width: auto; }
  [aria-invalid=true] { border-color: var(--error-color, #db4437); }
  .err { color: var(--error-color, #db4437); font-size: 0.8rem; min-height: 0; }
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
    this._timer = setInterval(() => this._load(), REFRESH_MS);
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
      const entries = await this._hass.callWS({ type: "config_entries/get", domain: "good_days" });
      this._entries = (entries || []).filter((e) => e.state === "loaded");
    } catch (e) {
      this._entries = [];
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
    await this._loadIcs();
    const msg = { type: "good_days/dates/list", language: langOf(this._hass) };
    if (this._entryId) msg.entry_id = this._entryId;
    try {
      const result = await this._hass.callWS(msg);
      this._dates = result.dates;
      this._error = null;
    } catch (err) {
      this._error = err && err.code === "not_loaded" ? "not_loaded" : "load_error";
    }
    this._render();
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
      this._entries.forEach((e) => select.appendChild(new Option(e.title, e.entry_id)));
      select.value = this._entryId;
      select.addEventListener("change", () => { this._entryId = select.value; this._load(); });
      toolbar.appendChild(select);
    }
    root.appendChild(toolbar);

    const main = mk("main");
    root.appendChild(main);
    this._renderMainAndIcs(main);
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
    list.setAttribute("aria-label", this._t("title"));
    this._dates.forEach((record) => list.appendChild(this._renderRow(record)));
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
    const year = mk("input");
    year.type = "number";
    year.inputMode = "numeric";
    year.min = "3000";
    year.max = "6500";
    year.step = "1";
    year.value = state.original_year;
    year.addEventListener("input", () => { state.original_year = year.value; clearError("original_year"); });
    hebrewBox.append(
      field("hebrew_day", this._t("day"), day),
      field("hebrew_month", this._t("month"), month),
      field("original_year", this._t("year"), year, this._t("year_hint")),
    );
    hebrewBox.querySelector(".field.original_year").classList.add("year");
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
          const y = Number(state.original_year);
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
          original_year: state.original_year === "" ? null : Number(state.original_year),
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
}

if (!customElements.get("good-days-panel")) {
  customElements.define("good-days-panel", GoodDaysPanel);
}
