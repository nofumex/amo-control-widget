import { escapeHtml } from "./html";

export function statusPage(status: Record<string, unknown>): string {
  return `
    <div class="acw-status">
      ${row("amoCRM", status.oauth_connected ? "подключен" : "не подключен")}
      ${row("Режим", status.mode)}
      ${row("Tenant/account", `${status.tenant_id || "-"} / ${status.account_id || "-"}`)}
      ${row("Last sync", status.last_sync)}
      ${row("Next sync", status.next_sync)}
      ${row("Last report", status.last_report_build)}
      ${row("Last Telegram", status.last_delivery)}
      ${row("Ошибка", status.latest_error || "-")}
      ${row("Сотрудников", status.enabled_users)}
      ${row("Telegram", status.telegram_enabled ? "включен" : "выключен")}
    </div>
    <div class="acw-actions">
      <button data-action="sync">Синхронизировать сейчас</button>
      <button data-action="build-today">Построить отчет за сегодня</button>
      <button data-action="open-last">Открыть последний отчет</button>
    </div>
  `;
}

function row(label: string, value: unknown): string {
  return `<div><strong>${escapeHtml(label)}</strong><span>${escapeHtml(value ?? "-")}</span></div>`;
}
