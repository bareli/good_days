/* Good Days card: upcoming Shabbat, holidays and family calendar events with countdowns. */

const REFRESH_MS = 5 * 60 * 1000;
const TICK_MS = 60 * 1000;
const FSI = "⁨"; // first-strong isolate
const PDI = "⁩";
const iso = (text) => FSI + text + PDI;

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
    e_title: "Title",
    e_calendars: "Calendars to merge",
    e_days: "Days ahead",
    e_limit: "Maximum items",
    e_categories: "Holiday categories (empty = integration settings)",
    e_show_hebrew_date: "Show Hebrew date",
    e_show_candle_lighting: "Show candle lighting",
    e_compact: "Compact (one line)",
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
    e_title: "כותרת",
    e_calendars: "לוחות שנה לשילוב",
    e_days: "ימים קדימה",
    e_limit: "מספר פריטים מרבי",
    e_categories: "קטגוריות חגים (ריק = הגדרות האינטגרציה)",
    e_show_hebrew_date: "הצגת תאריך עברי",
    e_show_candle_lighting: "הצגת זמן הדלקת נרות",
    e_compact: "תצוגה מקוצרת (שורה אחת)",
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
  .banner { display: flex; align-items: center; gap: 8px; padding: 8px 12px; margin-bottom: 10px; border-radius: 10px;
    background: color-mix(in srgb, var(--warning-color, #ff9800) 16%, transparent); color: var(--primary-text-color); font-weight: 500; }
  .hint, .warn { font-size: 0.85rem; color: var(--secondary-text-color); margin: 6px 0; }
  .warn { color: var(--error-color, #db4437); }
  .empty { color: var(--secondary-text-color); padding: 12px 0; }
  section { margin: 0 0 6px; }
  .day { display: flex; align-items: baseline; gap: 8px; margin: 10px 0 4px; }
  .day h3 { font-size: 0.9rem; font-weight: 600; margin: 0; color: var(--primary-text-color); }
  .hdate { font-size: 0.78rem; color: var(--secondary-text-color); }
  ul { list-style: none; margin: 0; padding: 0; }
  li { margin: 0; }
  button.item { all: unset; box-sizing: border-box; width: 100%; display: flex; align-items: center; gap: 10px;
    padding: 8px 6px; border-radius: 8px; cursor: pointer; color: var(--primary-text-color); }
  button.item:hover { background: var(--secondary-background-color); }
  button.item:focus-visible, button.compact:focus-visible { outline: 2px solid var(--primary-color); outline-offset: 2px; }
  .dot { width: 10px; height: 10px; border-radius: 50%; flex: none; }
  ha-icon.cat { --mdc-icon-size: 18px; color: var(--secondary-text-color); flex: none; }
  .main { flex: 1; min-width: 0; display: flex; flex-direction: column; gap: 2px; }
  .name { font-size: 0.95rem; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
  .meta { display: flex; flex-wrap: wrap; gap: 6px; font-size: 0.8rem; color: var(--secondary-text-color); }
  .badge { display: inline-flex; align-items: center; gap: 3px; }
  ha-icon.small { --mdc-icon-size: 14px; }
  .badge.conflict { color: var(--warning-color, #ff9800); }
  .chip { flex: none; font-size: 0.78rem; padding: 2px 8px; border-radius: 999px; white-space: nowrap;
    background: var(--secondary-background-color); color: var(--primary-text-color); }
  .chip.now { background: var(--primary-color); color: var(--text-primary-color, #fff); }
  .details { margin: 0 6px 8px; margin-inline-start: 26px; font-size: 0.85rem; color: var(--secondary-text-color); display: grid; gap: 2px; }
  .details .desc { white-space: pre-line; color: var(--primary-text-color); }
  button.compact { all: unset; box-sizing: border-box; width: 100%; display: flex; align-items: center; gap: 8px; cursor: pointer; }
  .ltr { direction: ltr; unicode-bidi: isolate; }
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
    this._tickTimer = setInterval(() => this._render(), TICK_MS);
    if (this._hass && this._config && !this._data) this._fetch();
  }

  disconnectedCallback() {
    clearInterval(this._refreshTimer);
    clearInterval(this._tickTimer);
  }

  getCardSize() {
    if (this._config && this._config.compact) return 1;
    return 2 + Math.min((this._data && this._data.items.length) || 3, this._config ? this._config.limit : 10);
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
    if (!this._hass || !this._config || this._loading) return;
    this._loading = true;
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
    try {
      this._data = await this._hass.callWS(msg);
      this._fallback = false;
      this._error = null;
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
    this._render();
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

  _startMs(item) {
    return item.all_day ? Date.parse(item.start + "T00:00:00") : Date.parse(item.start);
  }

  _endMs(item) {
    return item.all_day ? Date.parse(item.end + "T00:00:00") : Date.parse(item.end);
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
      const date = new Date(Date.UTC(+key.slice(0, 4), +key.slice(5, 7) - 1, +key.slice(8, 10), 12));
      const locale = langOf(this._hass) === "he" ? "he-IL-u-ca-hebrew-nu-hebr" : "en-u-ca-hebrew";
      return date.toLocaleDateString(locale, { day: "numeric", month: "long", timeZone: "UTC" });
    } catch (e) {
      return "";
    }
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

  _render() {
    if (!this._config) return;
    // Rebuilt on every tick; keep keyboard focus on the same control.
    const active = this.shadowRoot.activeElement;
    const focusKey = active ? active.getAttribute("data-focus-key") : null;
    this._renderInner();
    if (focusKey) {
      const again = this.shadowRoot.querySelector(`[data-focus-key="${CSS.escape(focusKey)}"]`);
      if (again) again.focus();
    }
  }

  _renderInner() {
    const lang = langOf(this._hass);
    const root = this.shadowRoot;
    root.textContent = "";
    root.appendChild(mk("style", null, STYLE));
    const card = document.createElement("ha-card");
    card.setAttribute("dir", lang === "he" ? "rtl" : "ltr");
    card.setAttribute("lang", lang);
    root.appendChild(card);

    const nowMs = Date.now();
    const todayKey = this._dayKey(new Date(nowMs));
    const items = ((this._data && this._data.items) || []).filter((i) => this._endMs(i) > nowMs);

    if (this._config.compact) {
      this._renderCompact(card, items, nowMs, todayKey);
      return;
    }

    const header = mk("div", "header");
    header.appendChild(mk("h2", "title", this._config.title || this._t("title")));
    card.appendChild(header);

    const current = this._data && this._data.current;
    if (current && this._endMs(current) > nowMs) {
      const banner = mk("div", "banner");
      banner.setAttribute("role", "status");
      const icon = document.createElement("ha-icon");
      icon.setAttribute("icon", "mdi:candle");
      const greeting = current.category === "yom_tov" ? this._t("chag_sameach") : this._t("shabbat_shalom");
      banner.append(icon, mk("span", null, `${greeting} · ${this._t("ends_at", this._time(current.end), current.category)}`));
      card.appendChild(banner);
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

    const groups = new Map();
    items.forEach((item) => {
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

  _icon(name) {
    const icon = document.createElement("ha-icon");
    icon.className = "small";
    icon.setAttribute("icon", name);
    icon.setAttribute("aria-hidden", "true");
    return icon;
  }

  _renderItem(item, nowMs, todayKey) {
    const li = mk("li");
    const button = mk("button", "item");
    button.type = "button";
    const detailsId = `details-${item.uid}`;
    const expanded = this._expanded.has(item.uid);
    button.setAttribute("aria-expanded", String(expanded));
    button.setAttribute("aria-controls", detailsId);
    button.setAttribute("data-focus-key", `item-${item.uid}`);
    button.addEventListener("click", () => {
      if (this._expanded.has(item.uid)) this._expanded.delete(item.uid);
      else this._expanded.add(item.uid);
      this._render();
    });

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
      // Shabbat / Yom Tov start at candle lighting: show that instead of a bare start time.
      const badge = mk("span", "badge");
      badge.append(this._icon("mdi:candle"), mk("span", null, this._t("candles", this._time(item.candle_lighting))));
      meta.appendChild(badge);
    } else {
      meta.appendChild(mk("span", null, item.all_day ? this._t("all_day") : iso(this._time(item.start))));
    }
    if (item.conflicts_shabbat) {
      const badge = mk("span", "badge conflict");
      badge.append(this._icon("mdi:alert-outline"), mk("span", null, this._t("on_shabbat")));
      meta.appendChild(badge);
    }
    main.appendChild(meta);
    button.appendChild(main);

    const countdown = this._countdown(item, nowMs, todayKey);
    button.appendChild(mk("span", countdown.now ? "chip now" : "chip", countdown.text));
    li.appendChild(button);

    const details = mk("div", "details");
    details.id = detailsId;
    details.hidden = !expanded;
    if (expanded) {
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
    li.appendChild(details);
    return li;
  }

  _renderCompact(card, items, nowMs, todayKey) {
    const item = items[0];
    const row = mk("button", "compact");
    row.type = "button";
    row.setAttribute("data-focus-key", "compact");
    row.style.padding = "4px 0";
    if (!item) {
      row.appendChild(mk("span", null, this._data ? this._t("empty") : this._t("loading")));
    } else {
      const dot = mk("span", "dot");
      dot.style.background = this._color(item);
      dot.setAttribute("aria-hidden", "true");
      const parts = [`${this._t("next")}: ${item.title}`, this._countdown(item, nowMs, todayKey).text];
      if (this._config.show_candle_lighting !== false && item.candle_lighting) parts.push(this._t("candles", this._time(item.candle_lighting)));
      else if (!item.all_day) parts.push(iso(this._time(item.start)));
      row.append(dot, mk("span", "name", parts.join(" · ")));
    }
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

  _schema() {
    return [
      { name: "title", selector: { text: {} } },
      { name: "calendars", selector: { entity: { domain: "calendar", multiple: true } } },
      { name: "days", selector: { number: { min: 1, max: 400, mode: "box" } } },
      { name: "limit", selector: { number: { min: 1, max: 100, mode: "box" } } },
      {
        name: "categories",
        selector: {
          select: { multiple: true, mode: "list", options: CATEGORIES.map((c) => ({ value: c, label: this._t(`c_${c}`) })) },
        },
      },
      { name: "show_hebrew_date", selector: { boolean: {} } },
      { name: "show_candle_lighting", selector: { boolean: {} } },
      { name: "compact", selector: { boolean: {} } },
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
        Object.keys(value).forEach((k) => {
          if (value[k] === "" || value[k] == null || (Array.isArray(value[k]) && !value[k].length && k !== "calendars")) delete value[k];
        });
        this._config = value;
        this.dispatchEvent(new CustomEvent("config-changed", { detail: { config: value }, bubbles: true, composed: true }));
      });
      this.appendChild(this._form);
    }
    this._form.hass = this._hass;
    this._form.schema = this._schema();
    this._form.data = Object.assign({ show_hebrew_date: true, show_candle_lighting: true, compact: false }, this._config);
  }
}

if (!customElements.get("good-days-card-editor")) {
  customElements.define("good-days-card-editor", GoodDaysCardEditor);
}
if (!customElements.get("good-days-card")) {
  customElements.define("good-days-card", GoodDaysCard);
  window.customCards = window.customCards || [];
  window.customCards.push({
    type: "good-days-card",
    name: "Good Days",
    description: "Upcoming Shabbat, holidays and family events with countdowns.",
    preview: true,
    documentationURL: "https://github.com/bareli/good_days",
  });
}
