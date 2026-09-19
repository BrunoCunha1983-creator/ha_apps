# Timezone & Clock Change for Home Assistant

Custom integration for Home Assistant that tracks timezone, UTC offset and daylight-saving-time changes.

It can use:

- Home Assistant's configured timezone;
- a fixed IANA timezone such as `Europe/Lisbon`;
- a moving `device_tracker` with `latitude` and `longitude`, useful for a motorhome, car, phone or other GPS tracker.

## Main entities

Each configured source creates timezone/local-time/UTC-offset sensors, a DST binary sensor, next/previous clock-change sensors, an event entity and a calendar.

## Mobile mode

Select a `device_tracker` which exposes `latitude` and `longitude`. The integration resolves the IANA timezone locally using `tzfpy`, so no external timezone API is required.

When the tracker crosses a timezone boundary, the integration updates the timezone and emits `timezone_changed`. If the UTC offset changes, it also emits `offset_changed`.

## Installation for testing

Copy `custom_components/timezone_change` to `/config/custom_components/`, restart Home Assistant, then add **Timezone & Clock Change** from Settings → Devices & services.

## Monorepo

This copy lives inside the `ha_apps` monorepo under `integrations/timezone_change`. For HACS distribution it can be published/synchronised to a standalone repository automatically.

## Notes

- Refreshes once per minute.
- GPS mode refreshes immediately when the selected `device_tracker` changes.
- Keeps the last known timezone if the tracker becomes temporarily unavailable.
- Uses two-sample hysteresis near timezone borders to reduce GPS flapping.
- Timezone transition rules come from Python `zoneinfo`.

## Events

- `timezone_changed`
- `offset_changed`
- `dst_started`
- `dst_ended`

## License

MIT
