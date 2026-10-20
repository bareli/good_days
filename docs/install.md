# Install

## With HACS

1. Open **HACS** and search for **Good Days**.
2. Open it and choose **Download**.
3. Restart Home Assistant.

!!! tip "Not found in the HACS search?"
    Add it as a custom repository: in HACS open the menu (three dots), choose **Custom repositories**, enter `https://github.com/bareli/good_days`, pick the category **Integration**, and then install **Good Days**.

## Manually

Copy the folder `custom_components/good_days` from the [repository](https://github.com/bareli/good_days) into `<config>/custom_components/` and restart Home Assistant.

## Add the integration

Go to **Settings → Devices & services → Add integration → Good Days**.

If the core **Jewish Calendar** integration is already configured, its location, diaspora setting and candle lighting / havdalah minutes are offered as defaults. They are copied once and are not linked afterwards.

After setup, a **Good Days** entry appears in the sidebar (family dates and Shabbat timers), and the card `custom:good-days-card` is available for your dashboards.

## Dashboards in YAML mode

The card resource is registered automatically on storage-mode dashboards. On YAML-mode dashboards, add `/good_days_static/card.js` as a JavaScript module resource. See [Card](card.md).

## Optional: Assist and blueprints

- Assist sentences need a copy of two files, see [Assist](entities.md#assist).
- Blueprints are imported with one click, see [Blueprints](entities.md#blueprints).
