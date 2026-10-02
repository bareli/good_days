/* Good Days card: upcoming Shabbat, holidays and family calendar events with countdowns. */

const REFRESH_MS = 5 * 60 * 1000;
const TICK_MS = 60 * 1000;
// Card width tiers (px): below MEDIUM_PX secondary details hide, below NARROW_PX the list is capped too.
const MEDIUM_PX = 400;
const NARROW_PX = 280;
const DEFAULT_NARROW_LIMIT = 3;
const FSI = "\u2068"; // first-strong isolate
const PDI = "\u2069";
const iso = (text) => FSI + text + PDI;
const NBSP = "\u00a0"; // keeps "Haftarah:" on the line of its citation

const CATEGORIES = ["shabbat", "yom_tov", "chol_hamoed", "minor", "fast", "rosh_chodesh", "modern", "memorial", "erev", "family"];
const KIND_ICONS = { birthday: "mdi:cake-variant", yahrzeit: "mdi:candle", anniversary: "mdi:ring", custom: "mdi:calendar-heart" };
const CATEGORY_ICONS = {
  shabbat: "mdi:candle",
  yom_tov: "mdi:star-david",
  chol_hamoed: "mdi:home-roof",
  minor: "mdi:party-popper",
  fast: "mdi:food-off-outline",
  rosh_chodesh: "mdi:moon-waxing-crescent",
  modern: "mdi:flag-variant",
  memorial: "mdi:candle",
  erev: "mdi:weather-sunset",
};
const PALETTE = ["#4caf50", "#2196f3", "#ff9800", "#9c27b0", "#009688", "#e91e63", "#795548", "#607d8b"];
// Integration default (const.DEFAULT_CATEGORIES) + family: used by the editor when the server does not say.
const DEFAULT_EFFECTIVE = ["shabbat", "yom_tov", "chol_hamoed", "minor", "fast", "modern", "family"];
// Intl "en-u-ca-hebrew" month names -> storage month keys.
const INTL_MONTHS = {
  Tishri: "tishrei", Heshvan: "marcheshvan", Kislev: "kislev", Tevet: "tevet", Shevat: "shvat", Adar: "adar",
  "Adar I": "adar_i", "Adar II": "adar_ii", Nisan: "nisan", Iyar: "iyyar", Sivan: "sivan", Tamuz: "tammuz", Av: "av", Elul: "elul",
};
const MONTH_NAMES = {
  en: {
    tishrei: "Tishrei", marcheshvan: "Cheshvan", kislev: "Kislev", tevet: "Tevet", shvat: "Shvat", adar: "Adar", adar_i: "Adar I",
    adar_ii: "Adar II", nisan: "Nisan", iyyar: "Iyar", sivan: "Sivan", tammuz: "Tammuz", av: "Av", elul: "Elul",
  },
  he: {
    tishrei: "תשרי", marcheshvan: "חשוון", kislev: "כסלו", tevet: "טבת", shvat: "שבט", adar: "אדר", adar_i: "אדר א׳",
    adar_ii: "אדר ב׳", nisan: "ניסן", iyyar: "אייר", sivan: "סיוון", tammuz: "תמוז", av: "אב", elul: "אלול",
  },
};

// Day of the Hebrew month (1-30) in gematria with geresh / gershayim: 1 -> א׳, 15 -> ט״ו, 22 -> כ״ב.
function gematriaDay(n) {
  const units = ["", "א", "ב", "ג", "ד", "ה", "ו", "ז", "ח", "ט"];
  const tens = ["", "י", "כ", "ל"];
  const letters = n === 15 ? "טו" : n === 16 ? "טז" : tens[Math.floor(n / 10)] + units[n % 10];
  return letters.length > 1 ? `${letters.slice(0, -1)}״${letters.slice(-1)}` : `${letters}׳`;
}

// Hebrew calendar day and month key of a "YYYY-MM-DD" civil day (Intl ignores nu-hebr, so parts only).
function hebrewParts(key) {
  const date = new Date(Date.UTC(+key.slice(0, 4), +key.slice(5, 7) - 1, +key.slice(8, 10), 12));
  const parts = new Intl.DateTimeFormat("en-u-ca-hebrew", { day: "numeric", month: "long", timeZone: "UTC" }).formatToParts(date);
  const get = (t) => (parts.find((p) => p.type === t) || {}).value;
  return { day: parseInt(get("day"), 10), month: INTL_MONTHS[get("month")] };
}

const I18N = {
  en: {
    title: "What's coming",
    today: "Today",
    tomorrow: "Tomorrow",
    all_day: "All day",
    now: "Now",
    in_min: (n) => `in ${iso(n)} min`,
    in_hours: (n) => `in ${iso(n)} h`,
    in_days: (n) => `in ${iso(n)} days`,
    shabbat_shalom: "Shabbat Shalom",
    chag_sameach: "Chag Sameach",
    ends_at: (t) => `ends ${iso(t)}`,
    candles: (t) => `Candles ${iso(t)}`,
    havdalah: (t) => `Havdalah ${iso(t)}`,
    yahrzeit_begins: (t) => `Begins at sunset ${iso(t)}`,
    yahrzeit_light: (t) => `light the memorial candle before ${iso(t)}`,
    moved: (from, to) => `(${from} falls on ${to} this year)`,
    hebrew_day: (day, month) => `${month} ${iso(day)}`,
    on_shabbat: "On Shabbat / Yom Tov",
    empty: "Nothing coming up",
    loading: "Loading…",
    error: "Could not load events",
    no_integration: "Install the Good Days integration to see Shabbat and holidays.",
    calendar_error: (name) => `Could not read ${name}`,
    next: "Next",
    source_holidays: "Jewish holidays",
    source_family: "Family dates",
    details_calendar: "Calendar",
    details_location: "Location",
    details_hebrew: "Hebrew date",
    haftarah: "Haftarah",
    e_title: "Title",
    e_calendars: "Calendars to merge",
    e_days: "Days ahead",
    e_limit: "Maximum items",
    e_use_integration_categories: "Use Good Days settings",
    e_categories: "Holiday categories",
    e_show_hebrew_date: "Show Hebrew date",
    e_show_candle_lighting: "Show candle lighting",
    e_show_haftarah: "Show haftarah",
    e_compact: "Compact (one line)",
    e_responsive: "Show less when the card is narrow",
    e_narrow_limit: "Events in a narrow card",
    e_entry_id: "Good Days instance",
    c_shabbat: "Shabbat",
    c_yom_tov: "Yom Tov",
    c_chol_hamoed: "Chol HaMoed",
    c_minor: "Minor holidays",
    c_fast: "Fast days",
    c_rosh_chodesh: "Rosh Chodesh",
    c_modern: "Israeli national days",
    c_memorial: "Other memorial days",
    c_erev: "Erev Yom Tov",
    c_family: "Family dates",
  },
  he: {
    title: "מה מתקרב",
    today: "היום",
    tomorrow: "מחר",
    all_day: "כל היום",
    now: "עכשיו",
    in_min: (n) => `בעוד ${iso(n)} דק׳`,
    in_hours: (n) => `בעוד ${iso(n)} שע׳`,
    in_days: (n) => (n === 2 ? "בעוד יומיים" : `בעוד ${iso(n)} ימים`),
    shabbat_shalom: "שבת שלום",
    chag_sameach: "חג שמח",
    ends_at: (t, category) => `${category === "yom_tov" ? "יוצא" : "יוצאת"} ב-${iso(t)}`,
    candles: (t) => `הדלקת נרות ${iso(t)}`,
    havdalah: (t) => `הבדלה ${iso(t)}`,
    yahrzeit_begins: (t) => `מתחיל בשקיעה ${iso(t)}`,
    yahrzeit_light: (t) => `הדלקת נר נשמה לפני ${iso(t)}`,
    moved: (from, to) => `(${from} חל השנה ב${to})`,
    hebrew_day: (day, month) => `${gematriaDay(day)} ${month}`,
    on_shabbat: "חל בשבת / חג",
    empty: "אין אירועים קרובים",
    loading: "טוען…",
    error: "לא ניתן לטעון אירועים",
    no_integration: "התקינו את האינטגרציה ימים טובים כדי לראות שבתות וחגים.",
    calendar_error: (name) => `לא ניתן לקרוא את ${name}`,
    next: "הבא",
    source_holidays: "חגי ישראל",
    source_family: "תאריכים משפחתיים",
    details_calendar: "לוח שנה",
    details_location: "מיקום",
    details_hebrew: "תאריך עברי",
    haftarah: "הפטרה",
    e_title: "כותרת",
    e_calendars: "לוחות שנה לשילוב",
    e_days: "ימים קדימה",
    e_limit: "מספר פריטים מרבי",
    e_use_integration_categories: "לפי הגדרות ימים טובים",
    e_categories: "קטגוריות חגים",
    e_show_hebrew_date: "הצגת תאריך עברי",
    e_show_candle_lighting: "הצגת זמן הדלקת נרות",
    e_show_haftarah: "הצגת ההפטרה",
    e_compact: "תצוגה מקוצרת (שורה אחת)",
    e_responsive: "הצגת פחות פרטים כשהכרטיס צר",
    e_narrow_limit: "מספר אירועים בכרטיס צר",
    e_entry_id: "מופע ימים טובים",
    c_shabbat: "שבת",
    c_yom_tov: "יום טוב",
    c_chol_hamoed: "חול המועד",
    c_minor: "חגים קטנים",
    c_fast: "צומות",
    c_rosh_chodesh: "ראש חודש",
    c_modern: "ימים לאומיים",
    c_memorial: "ימי זיכרון נוספים",
    c_erev: "ערבי חג",
    c_family: "תאריכים משפחתיים",
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

const STYLE = `
  :host { display: block; }
  ha-card { padding: 12px 16px 8px; overflow: hidden; }
  .header { display: flex; align-items: baseline; justify-content: space-between; gap: 8px; margin-bottom: 8px; }
  .title { font-size: 1.15rem; font-weight: 500; color: var(--primary-text-color); margin: 0; }
  .banner { display: flex; align-items: center; gap: 8px; padding: 10px 12px; margin-bottom: 10px; border-radius: 10px;
    background: color-mix(in srgb, var(--warning-color, #ff9800) 16%, transparent); color: var(--primary-text-color);
    font-size: 1.25rem; font-weight: 500; }
  .summary { display: grid; gap: 4px; padding: 10px 12px; margin-bottom: 10px; border-radius: 10px;
    border-inline-start: 4px solid var(--primary-color);
    background: color-mix(in srgb, var(--primary-color) 10%, var(--card-background-color, #fff)); color: var(--primary-text-color); }
  .summary .s-head { display: flex; align-items: center; gap: 8px; }
  .summary .s-title { flex: 1; min-width: 0; font-size: 1rem; font-weight: 500; overflow-wrap: anywhere; }
  .summary .s-times { display: flex; flex-wrap: wrap; align-items: center; column-gap: 12px; row-gap: 2px; font-size: 1.35rem; font-weight: 500; }
  .summary .s-times span { display: inline-flex; align-items: center; gap: 6px; }
  .hint, .warn { font-size: 0.85rem; color: var(--secondary-text-color); margin: 6px 0; }
  /* Theme error / warning colours are fills; mixed toward the text colour they read >= 4.5:1 in light and dark. */
  .warn { color: color-mix(in srgb, var(--error-color, #db4437) 75%, var(--primary-text-color, #212121)); }
  .empty { color: var(--secondary-text-color); padding: 12px 0; }
  section { margin: 0 0 6px; }
  .day { display: flex; flex-wrap: wrap; align-items: baseline; column-gap: 8px; margin: 10px 0 4px; }
  .day h3 { font-size: 0.9rem; font-weight: 600; margin: 0; color: var(--primary-text-color); }
  .hdate { font-size: 0.9rem; color: var(--secondary-text-color); }
  ul { list-style: none; margin: 0; padding: 0; }
  li { margin: 0; }
  button.item { all: unset; box-sizing: border-box; width: 100%; display: flex; align-items: center; gap: 10px;
    padding: 8px 6px; border-radius: 8px; cursor: pointer; color: var(--primary-text-color); }
  button.item:hover { background: var(--secondary-background-color); }
  button.item:focus-visible, button.compact:focus-visible { outline: 2px solid var(--primary-color); outline-offset: 2px; }
  .dot { width: 10px; height: 10px; border-radius: 50%; flex: none; }
  ha-icon.cat { --mdc-icon-size: 18px; color: var(--secondary-text-color); flex: none; }
  .main { flex: 1; min-width: 0; display: flex; flex-direction: column; gap: 2px; }
  .name { font-size: 0.95rem; white-space: normal; overflow-wrap: anywhere; }
  .meta { display: flex; flex-wrap: wrap; column-gap: 8px; row-gap: 2px; font-size: 0.93rem; color: var(--secondary-text-color); }
  .meta .time { color: var(--primary-text-color); }
  .badge { display: inline-flex; align-items: center; gap: 3px; }
  ha-icon.small { --mdc-icon-size: 14px; }
  .badge.conflict { color: color-mix(in srgb, var(--warning-color, #ff9800) 45%, var(--primary-text-color, #212121)); }
  .chip { flex: none; font-size: 0.9rem; padding: 2px 8px; border-radius: 999px; white-space: nowrap;
    background: var(--secondary-background-color); color: var(--primary-text-color); }
  .chip.now { background: color-mix(in srgb, var(--primary-color) 65%, black); color: #fff; }
  .summary .s-haftarah { font-size: 0.95rem; overflow-wrap: break-word; }
  .haftarah { font-size: 0.93rem; color: var(--secondary-text-color); overflow-wrap: break-word; }
  .details { margin: 0 6px 8px; margin-inline-start: 26px; font-size: 0.93rem; color: var(--secondary-text-color); display: grid; gap: 2px; }
  .details .desc { white-space: pre-line; color: var(--primary-text-color); }
  button.compact { all: unset; box-sizing: border-box; width: 100%; display: flex; align-items: flex-start; gap: 8px; cursor: pointer;
    padding: 4px 0; color: var(--primary-text-color); }
  button.compact .dot { margin-top: calc(0.7em - 5px); }
  button.compact .name { flex: 1; min-width: 0; line-height: 1.4; white-space: normal; overflow-wrap: anywhere; }
  .ltr { direction: ltr; unicode-bidi: isolate; }
  /* Width tiers (set from the card's own width): secondary details step out first; tapping a row still shows them. */
  ha-card[data-size="medium"] { padding: 10px 12px 6px; }
  ha-card[data-size="medium"] ha-icon.cat,
  ha-card[data-size="medium"] .haftarah { display: none; }
  ha-card:not([data-size="wide"]) .badge.conflict span { position: absolute; width: 1px; height: 1px; overflow: hidden; clip-path: inset(50%); white-space: nowrap; }
  ha-card[data-size="medium"] .summary .s-times { font-size: 1.15rem; }
  ha-card[data-size="narrow"] { padding: 8px 10px 4px; }
  ha-card[data-size="narrow"] .title { font-size: 1rem; }
  ha-card[data-size="narrow"] .header { margin-bottom: 4px; }
  ha-card[data-size="narrow"] ha-icon.cat,
  ha-card[data-size="narrow"] .haftarah,
  ha-card[data-size="narrow"] .hdate,
  ha-card[data-size="narrow"] .summary .s-haftarah,
  ha-card[data-size="narrow"] .meta .extra { display: none; }
  ha-card[data-size="narrow"] .banner { font-size: 1rem; padding: 8px 10px; }
  ha-card[data-size="narrow"] .summary { padding: 8px 10px; }
  ha-card[data-size="narrow"] .summary .s-times { font-size: 1.05rem; }
  ha-card[data-size="narrow"] .day { margin: 6px 0 2px; }
  ha-card[data-size="narrow"] button.item { padding: 6px 4px; gap: 8px; }
  ha-card[data-size="narrow"] .meta .chip { font-size: 0.8rem; padding: 0 6px; }
  ha-card[data-size="narrow"] .details { margin-inline-start: 18px; }
  @media (prefers-reduced-motion: no-preference) { button.item { transition: background-color 0.15s; } }
`;

class GoodDaysCard extends HTMLElement {
  static getConfigElement() { return document.createElement("good-days-card-editor"); }
  static getStubConfig() {
    return { days: 30, limit: 10, calendars: [], show_hebrew_date: true, show_candle_lighting: true };
  }

  constructor() {
    super();
    this.attachShadow({ mode: "open" });
    this._data = null;
    this._error = null;
    this._fallback = false;
    this._expanded = new Set();
    this._signature = "";
    this._loading = false;
    this._updaters = [];
  }

  setConfig(config) {
    if (!config || typeof config !== "object") throw new Error("Invalid configuration");
    if (config.calendars != null && !Array.isArray(config.calendars)) throw new Error("calendars must be a list");
    this._config = Object.assign({ days: 30, limit: 10, show_hebrew_date: true, show_candle_lighting: true }, config);
    this._data = null;
    if (this._hass) this._fetch();
  }

  set hass(hass) {
    const first = !this._hass;
    this._hass = hass;
    const sig = this._watchSignature();
    if (first || sig !== this._signature) {
      this._signature = sig;
      this._fetch();
    }
  }

  connectedCallback() {
    this._refreshTimer = setInterval(() => this._fetch(), REFRESH_MS);
    this._tickTimer = setInterval(() => this._tick(), TICK_MS);
    if (typeof ResizeObserver === "function") {
      this._resizeObserver = this._resizeObserver || new ResizeObserver((entries) => this._onResize(entries[0].contentRect.width));
      this._resizeObserver.observe(this);
    }
    if (this._hass && this._config && !this._data) this._fetch();
  }

  disconnectedCallback() {
    clearInterval(this._refreshTimer);
    clearInterval(this._tickTimer);
    if (this._resizeObserver) this._resizeObserver.disconnect();
  }

  getCardSize() {
    if (this._config && this._config.compact) return 1;
    const shown = Math.min((this._data && this._data.items.length) || 3, this._itemLimit());
    return 2 + shown;
  }

  // Sections view: full width by default, usable down to a quarter of a section.
  getGridOptions() {
    if (this._config && this._config.compact) return { columns: 12, rows: 1, min_columns: 3, min_rows: 1 };
    return { columns: 12, min_columns: 3 };
  }

  // wide / medium / narrow from the card's own width (not the screen): a card in a narrow column shows less.
  _sizeFor(width) {
    if (!this._config || this._config.responsive === false) return "wide";
    if (width < NARROW_PX) return "narrow";
    if (width < MEDIUM_PX) return "medium";
    return "wide";
  }

  _onResize(width) {
    if (!width) return; // hidden (other view, closed edit dialog): keep the last layout
    const size = this._sizeFor(width);
    if (size === this._size) return;
    this._size = size;
    if (this._shadowRendered) this._render();
  }

  _currentSize() {
    return this._config && this._config.responsive === false ? "wide" : this._size || "wide";
  }

  // The configured limit, capped in a narrow card (narrow_limit, default 3).
  _itemLimit() {
    const limit = this._config ? Number(this._config.limit) || 10 : 10;
    if (this._currentSize() !== "narrow") return limit;
    return Math.min(limit, Math.max(1, Number(this._config.narrow_limit) || DEFAULT_NARROW_LIMIT));
  }

  _t(key, ...args) {
    const dict = I18N[langOf(this._hass)];
    const value = dict[key] != null ? dict[key] : I18N.en[key];
    return typeof value === "function" ? value(...args) : value;
  }

  _watchSignature() {
    if (!this._hass || !this._config) return "";
    const ids = [...(this._config.calendars || [])];
    Object.keys(this._hass.states).forEach((id) => {
      if (id.startsWith("calendar.good_days")) ids.push(id);
    });
    return ids.map((id) => {
      const s = this._hass.states[id];
      return s ? `${id}:${s.last_updated}` : id;
    }).join("|");
  }

  _timeZone() {
    const h = this._hass;
    return h && h.locale && h.locale.time_zone === "server" && h.config ? h.config.time_zone : undefined;
  }

  _locale() {
    return langOf(this._hass) === "he" ? "he-IL" : ((this._hass && this._hass.locale && this._hass.locale.language) || "en");
  }

  async _fetch() {
    if (!this._hass || !this._config) return;
    if (this._loading) {
      this._refetch = true; // config or data changed mid-request: fetch again afterwards
      return;
    }
    this._loading = true;
    this._refetch = false;
    const cfg = this._config;
    const msg = {
      type: "good_days/upcoming",
      calendars: cfg.calendars || [],
      days: Number(cfg.days) || 30,
      limit: Number(cfg.limit) || 10,
      language: langOf(this._hass),
    };
    if (cfg.entry_id) msg.entry_id = cfg.entry_id;
    if (Array.isArray(cfg.categories) && cfg.categories.length) msg.categories = cfg.categories;
    const before = JSON.stringify([this._data, this._fallback, !!this._error]);
    try {
      this._data = await this._hass.callWS(msg);
      this._fallback = false;
      this._error = null;
      await this._fetchMoves(msg);
    } catch (err) {
      if (err && (err.code === "unknown_command" || err.code === "not_loaded")) {
        this._fallback = true;
        try {
          this._data = await this._fetchRest(msg);
          this._error = null;
        } catch (err2) {
          this._error = err2;
        }
      } else {
        this._error = err;
      }
    } finally {
      this._loading = false;
    }
    if (this._refetch) {
      this._fetch();
      return;
    }
    // Same answer as before (the 5-minute refresh, most of the time): only update the countdowns.
    if (this._shadowRendered && JSON.stringify([this._data, this._fallback, !!this._error]) === before) this._tick();
    else this._render();
  }

  // Stored Hebrew day / month of the family dates on screen, to say when a rule moved this year's date.
  async _fetchMoves(msg) {
    const ids = new Set(((this._data && this._data.items) || []).filter((i) => i.source === "family" && i.date_id).map((i) => i.date_id));
    if (!ids.size) return;
    const key = `${msg.entry_id || ""}|${[...ids].sort().join(",")}`;
    const cache = this._storedCache;
    if (!cache || cache.key !== key || Date.now() - cache.at > 60 * 60 * 1000) {
      try {
        const query = { type: "good_days/dates/list" };
        if (msg.entry_id) query.entry_id = msg.entry_id;
        const result = await this._hass.callWS(query);
        const stored = {};
        ((result && result.dates) || []).forEach((d) => {
          if (ids.has(d.id)) stored[d.id] = { day: d.hebrew_day, month: d.hebrew_month };
        });
        this._storedCache = { key, at: Date.now(), stored };
      } catch (err) {
        return; // Optional detail only.
      }
    }
    this._data = Object.assign({}, this._data, { _stored: this._storedCache.stored });
  }

  // Without the integration: plain calendar events over REST, no holidays.
  async _fetchRest(msg) {
    const now = new Date();
    const end = new Date(now.getTime() + msg.days * 86400000);
    const items = [];
    const errors = [];
    await Promise.all(msg.calendars.map(async (entityId) => {
      try {
        const events = await this._hass.callApi(
          "GET",
          `calendars/${entityId}?start=${encodeURIComponent(now.toISOString())}&end=${encodeURIComponent(end.toISOString())}`,
        );
        (events || []).forEach((ev) => {
          const allDay = !!(ev.start && ev.start.date);
          items.push({
            uid: `${entityId}-${ev.uid || ""}-${(ev.start && (ev.start.dateTime || ev.start.date)) || ""}`,
            source: entityId,
            title: ev.summary || "",
            start: allDay ? ev.start.date : ev.start.dateTime,
            end: allDay ? ev.end.date : ev.end.dateTime,
            all_day: allDay,
            description: ev.description || "",
            location: ev.location || "",
          });
        });
      } catch (err) {
        errors.push({ entity_id: entityId, error: String((err && err.message) || err) });
      }
    }));
    items.sort((a, b) => this._startMs(a) - this._startMs(b));
    return { items: items.slice(0, msg.limit), current: null, errors };
  }

  // Dates -------------------------------------------------------------------

  _dayKey(date) {
    const parts = new Intl.DateTimeFormat("en-CA", {
      timeZone: this._timeZone(), year: "numeric", month: "2-digit", day: "2-digit",
    }).formatToParts(date);
    const get = (t) => parts.find((p) => p.type === t).value;
    return `${get("year")}-${get("month")}-${get("day")}`;
  }

  // Epoch ms of local midnight of "YYYY-MM-DD" in the display time zone (server or browser).
  _midnightMs(key) {
    const wall = Date.UTC(+key.slice(0, 4), +key.slice(5, 7) - 1, +key.slice(8, 10));
    const format = new Intl.DateTimeFormat("en-CA", {
      timeZone: this._timeZone(), hourCycle: "h23",
      year: "numeric", month: "2-digit", day: "2-digit", hour: "2-digit", minute: "2-digit",
    });
    const offset = (ms) => {
      const parts = format.formatToParts(new Date(ms));
      const get = (t) => +parts.find((p) => p.type === t).value;
      return Date.UTC(get("year"), get("month") - 1, get("day"), get("hour"), get("minute")) - ms;
    };
    // Two passes: the zone offset at midnight itself, correct on DST change days.
    const first = wall - offset(wall);
    return wall - offset(first);
  }

  _startMs(item) {
    return item.all_day ? this._midnightMs(item.start) : Date.parse(item.start);
  }

  _endMs(item) {
    return item.all_day ? this._midnightMs(item.end) : Date.parse(item.end);
  }

  _itemDayKey(item) {
    return item.all_day ? item.start : this._dayKey(new Date(item.start));
  }

  _daysBetween(fromKey, toKey) {
    const [a, b] = [fromKey, toKey].map((k) => Date.UTC(+k.slice(0, 4), +k.slice(5, 7) - 1, +k.slice(8, 10)));
    return Math.round((b - a) / 86400000);
  }

  _time(value) {
    return new Date(value).toLocaleTimeString(this._locale(), {
      hour: "2-digit", minute: "2-digit", hourCycle: "h23", timeZone: this._timeZone(),
    });
  }

  _dayLabel(key, todayKey) {
    const diff = this._daysBetween(todayKey, key);
    if (diff <= 0) return this._t("today");
    if (diff === 1) return this._t("tomorrow");
    const date = new Date(Date.UTC(+key.slice(0, 4), +key.slice(5, 7) - 1, +key.slice(8, 10), 12));
    const weekday = date.toLocaleDateString(this._locale(), { weekday: "long", timeZone: "UTC" });
    return `${weekday} ${iso(`${+key.slice(8, 10)}.${+key.slice(5, 7)}`)}`;
  }

  _hebrewDayLabel(key) {
    try {
      if (langOf(this._hass) === "he") {
        // Browsers ignore "nu-hebr": build the gematria day ("כ״ב תשרי") from the Hebrew-calendar parts.
        const { day, month } = hebrewParts(key);
        if (day >= 1 && day <= 30 && month) return this._t("hebrew_day", day, MONTH_NAMES.he[month]);
      }
      const date = new Date(Date.UTC(+key.slice(0, 4), +key.slice(5, 7) - 1, +key.slice(8, 10), 12));
      return date.toLocaleDateString("en-u-ca-hebrew", { day: "numeric", month: "long", timeZone: "UTC" });
    } catch (e) {
      return "";
    }
  }

  // "(ל׳ חשוון חל השנה בא׳ כסלו)" when a family date's rule moved this year's occurrence.
  _movedNote(item) {
    const stored = item.source === "family" && this._data && this._data._stored && this._data._stored[item.date_id];
    const day = item.day || (item.all_day ? item.start : null);
    if (!stored || !day) return null;
    let actual;
    try {
      actual = hebrewParts(day.slice(0, 10));
    } catch (e) {
      return null;
    }
    const adar = (m) => (m === "adar" || m === "adar_i" || m === "adar_ii" ? "adar" : m);
    if (!actual.month || (actual.day === stored.day && adar(actual.month) === adar(stored.month))) return null;
    const lang = langOf(this._hass);
    const label = (d, m) => this._t("hebrew_day", d, MONTH_NAMES[lang][m] || m);
    return this._t("moved", label(stored.day, stored.month), label(actual.day, actual.month));
  }

  _countdown(item, nowMs, todayKey) {
    const start = this._startMs(item);
    if (start <= nowMs && nowMs < this._endMs(item)) return { text: this._t("now"), now: true };
    if (item.all_day) {
      const days = this._daysBetween(todayKey, item.start);
      if (days <= 0) return { text: this._t("today"), now: false };
      if (days === 1) return { text: this._t("tomorrow"), now: false };
      return { text: this._t("in_days", days), now: false };
    }
    const minutes = Math.max(1, Math.round((start - nowMs) / 60000));
    if (minutes < 60) return { text: this._t("in_min", minutes), now: false };
    if (minutes < 24 * 60) return { text: this._t("in_hours", Math.round(minutes / 60)), now: false };
    const days = this._daysBetween(todayKey, this._itemDayKey(item));
    return { text: days === 1 ? this._t("tomorrow") : this._t("in_days", days), now: false };
  }

  _color(item) {
    const colors = (this._config && this._config.colors) || {};
    if (colors[item.source]) return colors[item.source];
    if (item.source === "holidays") return colors.holidays || "var(--primary-color)";
    if (item.source === "family") return colors.family || "var(--accent-color, #ff9800)";
    const ids = this._config.calendars || [];
    const index = Math.max(0, ids.indexOf(item.source));
    return PALETTE[index % PALETTE.length];
  }

  _sourceName(item) {
    if (item.source === "holidays") return this._t("source_holidays");
    if (item.source === "family") return this._t("source_family");
    const state = this._hass.states[item.source];
    return (state && state.attributes.friendly_name) || item.source;
  }

  // Rendering ---------------------------------------------------------------

  // What is on screen besides countdown text: when it changes the tree is rebuilt, otherwise updated in place.
  _structureKey(nowMs) {
    const current = this._currentPeriod(nowMs);
    return [
      this._dayKey(new Date(nowMs)), langOf(this._hass), this._currentSize(), current ? current.uid : "",
      ...this._visibleItems(nowMs).map((i) => `${i.uid}@${this._startMs(i) <= nowMs ? 1 : 0}`),
    ].join("|");
  }

  _visibleItems(nowMs) {
    return ((this._data && this._data.items) || []).filter((i) => this._endMs(i) > nowMs);
  }

  _currentPeriod(nowMs) {
    const current = this._data && this._data.current;
    return current && this._endMs(current) > nowMs ? current : null;
  }

  // The one-minute tick: countdowns change every minute, the tree only when an item starts or ends.
  _tick() {
    if (!this._config) return;
    const nowMs = Date.now();
    if (!this._shadowRendered || this._structureKey(nowMs) !== this._renderedKey) {
      this._render();
      return;
    }
    const todayKey = this._dayKey(new Date(nowMs));
    this._updaters.forEach((update) => update(nowMs, todayKey));
  }

  _render() {
    if (!this._config) return;
    // A rebuild replaces the focused control: put keyboard focus back on its successor.
    const active = this.shadowRoot.activeElement;
    const focusKey = active ? active.getAttribute("data-focus-key") : null;
    this._renderInner();
    if (focusKey) this._restoreFocus(focusKey);
  }

  _restoreFocus(focusKey) {
    const find = () => this.shadowRoot.querySelector(`[data-focus-key="${CSS.escape(focusKey)}"]`);
    const target = find();
    if (!target) return;
    target.focus();
    if (this.shadowRoot.activeElement === target) return;
    // ha-card not upgraded / rendered yet (its slot is created asynchronously): try again once it is.
    const card = this._card;
    Promise.resolve(card && card.updateComplete)
      .then(() => new Promise((resolve) => requestAnimationFrame(resolve)))
      .then(() => {
        const again = find();
        const elsewhere = document.activeElement && document.activeElement !== document.body;
        if (again && !this.shadowRoot.activeElement && !elsewhere) again.focus();
      });
  }

  // ha-card is created once and kept: re-rendering only replaces its children, so a new control can take
  // focus immediately (a fresh ha-card has no slot until Lit renders it).
  _ensureCard() {
    const root = this.shadowRoot;
    if (!this._card || this._card.parentNode !== root) {
      root.textContent = "";
      root.appendChild(mk("style", null, STYLE));
      this._card = document.createElement("ha-card");
      root.appendChild(this._card);
    }
    return this._card;
  }

  _renderInner() {
    const lang = langOf(this._hass);
    const card = this._ensureCard();
    card.textContent = "";
    card.setAttribute("dir", lang === "he" ? "rtl" : "ltr");
    card.setAttribute("lang", lang);
    const size = this._currentSize();
    card.setAttribute("data-size", size);
    this._updaters = [];
    this._shadowRendered = true;

    const nowMs = Date.now();
    const todayKey = this._dayKey(new Date(nowMs));
    const items = this._visibleItems(nowMs);
    this._renderedKey = this._structureKey(nowMs);

    if (this._config.compact) {
      this._renderCompact(card, items, nowMs, todayKey);
      return;
    }

    const header = mk("div", "header");
    header.appendChild(mk("h2", "title", this._config.title || this._t("title")));
    card.appendChild(header);

    const current = this._currentPeriod(nowMs);
    let summarized = null;
    if (current) {
      const banner = mk("div", "banner");
      banner.setAttribute("role", "status");
      const icon = document.createElement("ha-icon");
      icon.setAttribute("icon", "mdi:candle");
      icon.setAttribute("aria-hidden", "true");
      const greeting = current.category === "yom_tov" ? this._t("chag_sameach") : this._t("shabbat_shalom");
      banner.append(icon, mk("span", null, `${greeting} · ${this._t("ends_at", this._time(current.end), current.category)}`));
      card.appendChild(banner);
    } else {
      summarized = this._renderSummary(card, items, nowMs, todayKey);
    }

    if (this._fallback) card.appendChild(mk("p", "hint", this._t("no_integration")));
    ((this._data && this._data.errors) || []).forEach((e) => {
      const state = this._hass.states[e.entity_id];
      const name = (state && state.attributes.friendly_name) || e.entity_id;
      card.appendChild(mk("p", "warn", this._t("calendar_error", name)));
    });

    if (!this._data) {
      card.appendChild(mk("p", "empty", this._error ? this._t("error") : this._t("loading")));
      return;
    }
    if (!items.length) {
      card.appendChild(mk("p", "empty", this._t("empty")));
      return;
    }

    // Smaller cards: the Shabbat / Yom Tov in the summary block is not repeated in the list.
    const listed = (size === "wide" || !summarized ? items : items.filter((i) => i !== summarized)).slice(0, this._itemLimit());
    const groups = new Map();
    listed.forEach((item) => {
      const key = this._startMs(item) <= nowMs ? todayKey : this._itemDayKey(item);
      if (!groups.has(key)) groups.set(key, []);
      groups.get(key).push(item);
    });

    groups.forEach((groupItems, key) => {
      const section = mk("section");
      const day = mk("div", "day");
      const headingId = `day-${key}`;
      const h3 = mk("h3", null, this._dayLabel(key, todayKey));
      h3.id = headingId;
      day.appendChild(h3);
      if (this._config.show_hebrew_date !== false) day.appendChild(mk("span", "hdate", this._hebrewDayLabel(key)));
      section.appendChild(day);
      const list = mk("ul");
      list.setAttribute("aria-labelledby", headingId);
      groupItems.forEach((item) => list.appendChild(this._renderItem(item, nowMs, todayKey)));
      section.appendChild(list);
      card.appendChild(section);
    });
  }

  // Next Shabbat / Yom Tov with candle lighting and havdalah, readable from across the kitchen.
  _renderSummary(card, items, nowMs, todayKey) {
    if (this._config.show_candle_lighting === false) return null;
    const next = items.find((i) => i.source === "holidays" && i.candle_lighting && this._startMs(i) > nowMs);
    if (!next) return null;
    const block = mk("div", "summary");
    block.setAttribute("role", "group");
    block.setAttribute("aria-label", next.title);
    const head = mk("div", "s-head");
    const icon = document.createElement("ha-icon");
    icon.setAttribute("icon", CATEGORY_ICONS[next.category] || "mdi:candle");
    icon.setAttribute("aria-hidden", "true");
    const chip = this._chip(next, nowMs, todayKey);
    head.append(icon, mk("span", "s-title", next.title), chip);
    const times = mk("div", "s-times");
    const candles = mk("span");
    candles.append(this._icon("mdi:candle"), mk("span", null, this._t("candles", this._time(next.candle_lighting))));
    times.appendChild(candles);
    if (next.havdalah) {
      const havdalah = mk("span");
      havdalah.append(this._icon("mdi:weather-night"), mk("span", null, this._t("havdalah", this._time(next.havdalah))));
      times.appendChild(havdalah);
    }
    block.append(head, times);
    const haftarah = this._haftarahLine(next);
    if (haftarah) block.appendChild(mk("div", "s-haftarah", haftarah));
    card.appendChild(block);
    return next;
  }

  // "Haftarah: ..." for a Shabbat (non-compact card); the server labels a Shabbat glued to Yom Tov.
  _haftarahLine(item) {
    if (this._config.show_haftarah === false || !item.haftarah) return null;
    const label = (item.haftarah_label || this._t("haftarah")).replace(/ /g, NBSP);
    return `${label}:${NBSP}${item.haftarah}`;
  }

  _icon(name) {
    const icon = document.createElement("ha-icon");
    icon.className = "small";
    icon.setAttribute("icon", name);
    icon.setAttribute("aria-hidden", "true");
    return icon;
  }

  // Countdown chip, kept current by the tick without rebuilding the row.
  _chip(item, nowMs, todayKey) {
    const chip = mk("span", "chip");
    const update = (now, today) => {
      const countdown = this._countdown(item, now, today);
      chip.textContent = countdown.text;
      chip.classList.toggle("now", countdown.now);
    };
    update(nowMs, todayKey);
    this._updaters.push(update);
    return chip;
  }

  // A yahrzeit starts at sunset: say so, and that the memorial candle is lit before it.
  _timeParts(item) {
    if (item.source === "family" && item.kind === "yahrzeit" && !item.all_day) {
      const time = this._time(item.start);
      return [this._t("yahrzeit_begins", time), this._t("yahrzeit_light", time)];
    }
    return [item.all_day ? this._t("all_day") : iso(this._time(item.start))];
  }

  _renderItem(item, nowMs, todayKey) {
    const li = mk("li");
    const button = mk("button", "item");
    button.type = "button";
    const detailsId = `details-${item.uid}`;
    button.setAttribute("aria-expanded", String(this._expanded.has(item.uid)));
    button.setAttribute("aria-controls", detailsId);
    button.setAttribute("data-focus-key", `item-${item.uid}`);

    const dot = mk("span", "dot");
    dot.style.background = this._color(item);
    dot.setAttribute("aria-hidden", "true");
    button.appendChild(dot);

    const iconName = item.source === "family" ? KIND_ICONS[item.kind] : item.source === "holidays" ? CATEGORY_ICONS[item.category] : null;
    if (iconName) {
      const icon = document.createElement("ha-icon");
      icon.className = "cat";
      icon.setAttribute("icon", iconName);
      icon.setAttribute("aria-hidden", "true");
      button.appendChild(icon);
    }

    const main = mk("span", "main");
    main.appendChild(mk("span", "name", item.title));
    const meta = mk("span", "meta");
    if (this._config.show_candle_lighting !== false && item.candle_lighting) {
      // Shabbat / Yom Tov start at candle lighting: show that and havdalah instead of a bare start time.
      const badge = mk("span", "badge time");
      badge.append(this._icon("mdi:candle"), mk("span", null, this._t("candles", this._time(item.candle_lighting))));
      meta.appendChild(badge);
      if (item.havdalah) {
        const end = mk("span", "badge time");
        end.append(this._icon("mdi:weather-night"), mk("span", null, this._t("havdalah", this._time(item.havdalah))));
        meta.appendChild(end);
      }
    } else {
      // Secondary parts ("extra") step out in a narrow card; the details still have them.
      this._timeParts(item).forEach((text, index) => meta.appendChild(mk("span", index ? "time extra" : "time", text)));
    }
    const moved = this._movedNote(item);
    if (moved) meta.appendChild(mk("span", "extra", moved));
    if (item.conflicts_shabbat) {
      const badge = mk("span", "badge conflict");
      badge.append(this._icon("mdi:alert-outline"), mk("span", null, this._t("on_shabbat")));
      meta.appendChild(badge);
    }
    main.appendChild(meta);
    const haftarah = this._haftarahLine(item);
    if (haftarah) main.appendChild(mk("span", "haftarah", haftarah));
    button.appendChild(main);
    // Narrow card: the countdown joins the time line, so the title gets the full width.
    const chip = this._chip(item, nowMs, todayKey);
    if (this._currentSize() === "narrow") meta.appendChild(chip);
    else button.appendChild(chip);
    li.appendChild(button);

    const details = mk("div", "details");
    details.id = detailsId;
    this._fillDetails(details, item);
    li.appendChild(details);

    // Toggled in place: the button keeps focus and screen readers hear the new aria-expanded state.
    button.addEventListener("click", () => {
      if (this._expanded.has(item.uid)) this._expanded.delete(item.uid);
      else this._expanded.add(item.uid);
      button.setAttribute("aria-expanded", String(this._expanded.has(item.uid)));
      this._fillDetails(details, item);
    });
    return li;
  }

  _fillDetails(details, item) {
    const expanded = this._expanded.has(item.uid);
    details.textContent = "";
    details.hidden = !expanded;
    if (!expanded) return;
    if (item.source === "holidays" || item.source === "family") {
      // Server description already has the Hebrew date (and candle lighting / havdalah, notes).
      if (item.description) details.appendChild(mk("span", "desc", item.description));
    } else {
      if (item.description) details.appendChild(mk("span", "desc", item.description));
      if (item.location) details.appendChild(mk("span", null, `${this._t("details_location")}: ${item.location}`));
      if (item.hebrew_date) details.appendChild(mk("span", null, `${this._t("details_hebrew")}: ${item.hebrew_date}`));
    }
    details.appendChild(mk("span", null, `${this._t("details_calendar")}: ${this._sourceName(item)}`));
  }

  // Compact line: the current Shabbat / Yom Tov, else the next candle lighting, else the next item.
  // The time leads, so a narrow screen wraps the titles, never the time; "Next" never goes with "now".
  _compactLine(items, nowMs, todayKey) {
    const current = this._currentPeriod(nowMs);
    if (current) {
      const greeting = current.category === "yom_tov" ? this._t("chag_sameach") : this._t("shabbat_shalom");
      return { item: current, text: `${greeting} · ${this._t("ends_at", this._time(current.end), current.category)}` };
    }
    const upcoming = items.filter((i) => this._startMs(i) > nowMs);
    const target = upcoming.find((i) => i.candle_lighting) || upcoming[0] || items[0];
    if (!target) return { item: null, text: this._data ? this._t("empty") : this._t("loading") };
    const parts = [];
    if (this._startMs(target) <= nowMs) {
      parts.push(this._countdown(target, nowMs, todayKey).text, target.title);
    } else {
      if (this._config.show_candle_lighting !== false && target.candle_lighting) parts.push(this._t("candles", this._time(target.candle_lighting)));
      else if (!target.all_day) parts.push(...this._timeParts(target));
      parts.push(this._countdown(target, nowMs, todayKey).text, `${this._t("next")}: ${target.title}`);
      const ongoing = items.find((i) => this._startMs(i) <= nowMs);
      if (ongoing) parts.push(ongoing.title);
    }
    return { item: target, text: parts.join(" · ") };
  }

  _renderCompact(card, items, nowMs, todayKey) {
    const line = this._compactLine(items, nowMs, todayKey);
    const item = line.item;
    const row = mk("button", "compact");
    row.type = "button";
    row.setAttribute("data-focus-key", "compact");
    if (item) {
      const dot = mk("span", "dot");
      dot.style.background = this._color(item);
      dot.setAttribute("aria-hidden", "true");
      row.appendChild(dot);
    }
    // One line where it fits; on a narrow screen it wraps rather than hide anything (WCAG 1.4.10).
    const name = mk("span", "name", line.text);
    row.appendChild(name);
    this._updaters.push((now, today) => {
      name.textContent = this._compactLine(items, now, today).text;
    });
    row.addEventListener("click", () => {
      this.dispatchEvent(new CustomEvent("hass-more-info", {
        detail: {
          entityId: !item || item.source === "holidays" ? "calendar.good_days_holidays"
            : item.source === "family" ? "calendar.good_days_family" : item.source,
        },
        bubbles: true, composed: true,
      }));
    });
    card.appendChild(row);
  }
}

class GoodDaysCardEditor extends HTMLElement {
  setConfig(config) {
    this._config = Object.assign({}, config);
    this._render();
  }

  set hass(hass) {
    this._hass = hass;
    if (this._form) this._form.hass = hass;
    else this._render();
  }

  _t(key) {
    const dict = I18N[langOf(this._hass)];
    return dict[key] != null ? dict[key] : I18N.en[key];
  }

  _followsIntegration() {
    return !Array.isArray(this._config.categories) || !this._config.categories.length;
  }

  // Categories the card shows when it follows the integration: the server's answer when it sends one,
  // otherwise the integration defaults + family dates.
  _effective() {
    const known = this._effectiveCache && this._effectiveCache.entry === (this._config.entry_id || "");
    if (!known && this._hass && !this._effectiveLoading) {
      const entry = this._config.entry_id || "";
      this._effectiveLoading = true;
      const msg = { type: "good_days/upcoming", days: 1, limit: 1, language: langOf(this._hass) };
      if (entry) msg.entry_id = entry;
      this._hass.callWS(msg)
        .then((result) => (result && Array.isArray(result.categories) ? result.categories : null), () => null)
        .then((categories) => {
          this._effectiveLoading = false;
          this._effectiveCache = { entry, categories: categories ? CATEGORIES.filter((c) => categories.includes(c)) : null };
          this._render();
        });
    }
    return (known && this._effectiveCache.categories) || DEFAULT_EFFECTIVE;
  }

  _schema() {
    return [
      { name: "title", selector: { text: {} } },
      { name: "calendars", selector: { entity: { domain: "calendar", multiple: true } } },
      { name: "days", selector: { number: { min: 1, max: 400, mode: "box" } } },
      { name: "limit", selector: { number: { min: 1, max: 100, mode: "box" } } },
      { name: "use_integration_categories", selector: { boolean: {} } },
      {
        name: "categories",
        selector: {
          select: { multiple: true, mode: "list", options: CATEGORIES.map((c) => ({ value: c, label: this._t(`c_${c}`) })) },
        },
      },
      { name: "show_hebrew_date", selector: { boolean: {} } },
      { name: "show_candle_lighting", selector: { boolean: {} } },
      { name: "show_haftarah", selector: { boolean: {} } },
      { name: "compact", selector: { boolean: {} } },
      { name: "responsive", selector: { boolean: {} } },
      { name: "narrow_limit", selector: { number: { min: 1, max: 20, mode: "box" } } },
      { name: "entry_id", selector: { config_entry: { integration: "good_days" } } },
    ];
  }

  _render() {
    if (!this._config || !this._hass) return;
    if (!this._form) {
      this._form = document.createElement("ha-form");
      this._form.computeLabel = (field) => this._t(`e_${field.name}`);
      this._form.addEventListener("value-changed", (ev) => {
        const value = Object.assign({}, ev.detail.value);
        const follows = this._followsIntegration();
        const shown = this._effective();
        const use = value.use_integration_categories;
        delete value.use_integration_categories;
        const same = (a, b) => a.length === b.length && a.every((c) => b.includes(c));
        if (follows && use === false) value.categories = [...shown]; // start from what the card shows now
        else if (!follows && use === true) delete value.categories;
        else if (follows && same(value.categories || [], shown)) delete value.categories;
        // Otherwise a box was ticked / unticked: the edited set becomes the card's own.
        Object.keys(value).forEach((k) => {
          if (value[k] === "" || value[k] == null || (Array.isArray(value[k]) && !value[k].length && k !== "calendars")) delete value[k];
        });
        this._config = value;
        this._render();
        this.dispatchEvent(new CustomEvent("config-changed", { detail: { config: value }, bubbles: true, composed: true }));
      });
      this.appendChild(this._form);
    }
    const follows = this._followsIntegration();
    this._form.hass = this._hass;
    this._form.schema = this._schema();
    this._form.data = Object.assign({ show_hebrew_date: true, show_candle_lighting: true, show_haftarah: true, compact: false, responsive: true }, this._config, {
      use_integration_categories: follows,
      categories: follows ? [...this._effective()] : this._config.categories,
    });
  }
}

// The card picker searches name and description: offer the Hebrew name in a Hebrew UI, keep "Good Days" in both.
function pickerHebrew() {
  const lang = (document.documentElement && document.documentElement.lang) || navigator.language || "en";
  return String(lang).toLowerCase().startsWith("he");
}

if (!customElements.get("good-days-card-editor")) {
  customElements.define("good-days-card-editor", GoodDaysCardEditor);
}
if (!customElements.get("good-days-card")) {
  customElements.define("good-days-card", GoodDaysCard);
  window.customCards = window.customCards || [];
  window.customCards.push({
    type: "good-days-card",
    get name() {
      return pickerHebrew() ? "ימים טובים (Good Days)" : "Good Days";
    },
    get description() {
      return pickerHebrew()
        ? "שבתות, חגים ותאריכים משפחתיים עם ספירה לאחור."
        : "Upcoming Shabbat, holidays and family events with countdowns.";
    },
    preview: true,
    documentationURL: "https://github.com/bareli/good_days",
  });
}
