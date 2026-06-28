export function settingsPage(settings: Record<string, unknown>): string {
  return `
    <div class="acw-grid">
      ${input("timezone", "Timezone", settings.timezone || "UTC")}
      ${input("work_session_gap_minutes", "Интервал непрерывной работы, мин", settings.work_session_gap_minutes || 10, "number")}
      ${input("incoming_call_min_duration_seconds", "Мин. входящий звонок, сек", settings.incoming_call_min_duration_seconds || 30, "number")}
      ${input("outgoing_call_min_duration_seconds", "Мин. исходящий звонок, сек", settings.outgoing_call_min_duration_seconds || 0, "number")}
      ${input("live_sync_interval_seconds", "Интервал live sync, сек", settings.live_sync_interval_seconds || 900, "number")}
      ${input("build_hour", "Час построения", settings.build_hour || 1, "number")}
      ${input("send_hour", "Час отправки", settings.send_hour || 9, "number")}
      <label class="acw-check"><input id="auto_send_enabled" type="checkbox" ${settings.auto_send_enabled ? "checked" : ""}> Автоотправка</label>
    </div>
    <button class="acw-primary" data-action="save-settings">Сохранить</button>
  `;
}

function input(id: string, label: string, value: unknown, type = "text"): string {
  return `<label><span>${label}</span><input id="${id}" type="${type}" value="${String(value)}"></label>`;
}
