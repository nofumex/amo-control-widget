import { WidgetApi } from "./api";
import { readWidgetSettings } from "./amo";
import { reportsPage } from "./reports_page";
import { settingsPage } from "./settings_page";
import { statusPage } from "./status_page";
import { telegramPage } from "./telegram_page";

type Tab = "status" | "settings" | "events" | "users" | "reports" | "telegram";

const tabs: Array<{ id: Tab; label: string }> = [
  { id: "status", label: "Статус" },
  { id: "settings", label: "Настройки отчета" },
  { id: "events", label: "События" },
  { id: "users", label: "Сотрудники" },
  { id: "reports", label: "Отчеты" },
  { id: "telegram", label: "Telegram" }
];

class App {
  private readonly api = new WidgetApi(readWidgetSettings());
  private root!: HTMLElement;
  private active: Tab = "status";
  private settings: Record<string, unknown> = {};

  async mount(root: HTMLElement) {
    this.root = root;
    this.root.className = "acw-root";
    await this.render();
    this.root.addEventListener("click", (event) => void this.handleClick(event));
  }

  async render(error = "") {
    const tabHtml = tabs.map((tab) => `<button class="${tab.id === this.active ? "active" : ""}" data-tab="${tab.id}">${tab.label}</button>`).join("");
    let panel = "";
    try {
      if (this.active === "status") panel = statusPage(await this.api.getStatus());
      if (this.active === "settings") {
        this.settings = await this.api.getSettings();
        panel = settingsPage(this.settings);
      }
      if (this.active === "events") panel = await this.eventsPanel();
      if (this.active === "users") panel = await this.usersPanel();
      if (this.active === "reports") panel = reportsPage();
      if (this.active === "telegram") panel = telegramPage(await this.api.getTelegram());
    } catch (err) {
      error = this.humanError(err);
      panel = "";
    }
    this.root.innerHTML = `${error ? `<div class="acw-error">${error}</div>` : ""}<div class="acw-tabs">${tabHtml}</div><div class="acw-panel">${panel}</div>`;
  }

  async eventsPanel() {
    this.settings = await this.api.getSettings();
    const catalog = await this.api.getEventCatalog();
    const rows = catalog.map((item) => {
      const code = String(item.code);
      return `
        <div><strong>${item.title_ru}</strong><br><small>${code}</small></div>
        ${check(`activity:${code}`, Boolean((this.settings.enabled_activity_events as Record<string, boolean>)?.[code]))}
        ${check(`counter:${code}`, Boolean((this.settings.enabled_counter_events as Record<string, boolean>)?.[code]))}
        ${check(`penalty:${code}`, Boolean((this.settings.enabled_penalty_events as Record<string, boolean>)?.[code]))}
      `;
    }).join("");
    return `<div class="acw-events"><div>Событие</div><div>Активность</div><div>Счетчик</div><div>Штраф</div>${rows}</div><button class="acw-primary" data-action="save-events">Сохранить</button>`;
  }

  async usersPanel() {
    const users = await this.api.getUsers();
    const rows = users.length ? users.map((user) => `<label class="acw-check"><input type="checkbox" data-user="${user.id}"> ${user.name || user.id}</label>`).join("") : "Пользователи появятся после подключения OAuth.";
    return `<input id="user_search" placeholder="Поиск"><div>${rows}</div><button class="acw-primary" data-action="save-users">Сохранить</button>`;
  }

  async handleClick(event: Event) {
    const target = event.target as HTMLElement;
    const tab = target.dataset.tab as Tab | undefined;
    if (tab) {
      this.active = tab;
      await this.render();
      return;
    }
    const action = target.dataset.action;
    if (!action) return;
    try {
      if (action === "sync") await this.api.syncNow();
      if (action === "build-today") await this.api.buildReport(new Date().toISOString().slice(0, 10));
      if (action === "save-settings") await this.saveSettings();
      if (action === "save-events") await this.saveEvents();
      if (action === "build-report") await this.buildReport();
      if (action === "load-report") await this.loadReport();
      if (action === "send-telegram") await this.sendTelegram();
      if (action === "copy-report") await navigator.clipboard.writeText(this.reportText());
      if (action === "save-telegram") await this.saveTelegram();
      if (action === "test-telegram") await this.api.testTelegram();
      await this.render();
    } catch (err) {
      await this.render(this.humanError(err));
    }
  }

  async saveSettings() {
    const payload = {
      ...this.settings,
      timezone: value("timezone"),
      work_session_gap_minutes: numberValue("work_session_gap_minutes"),
      incoming_call_min_duration_seconds: numberValue("incoming_call_min_duration_seconds"),
      outgoing_call_min_duration_seconds: numberValue("outgoing_call_min_duration_seconds"),
      live_sync_interval_seconds: numberValue("live_sync_interval_seconds"),
      build_hour: numberValue("build_hour"),
      send_hour: numberValue("send_hour"),
      auto_send_enabled: (document.getElementById("auto_send_enabled") as HTMLInputElement).checked
    };
    await this.api.saveSettings(payload);
  }

  async saveEvents() {
    const payload = { ...this.settings, enabled_activity_events: {}, enabled_counter_events: {}, enabled_penalty_events: {} };
    document.querySelectorAll<HTMLInputElement>("[data-event-key]").forEach((input) => {
      const [kind, code] = String(input.dataset.eventKey).split(":");
      const key = kind === "activity" ? "enabled_activity_events" : kind === "counter" ? "enabled_counter_events" : "enabled_penalty_events";
      (payload[key] as Record<string, boolean>)[code] = input.checked;
    });
    await this.api.saveSettings(payload);
  }

  async buildReport() {
    const data = await this.api.buildReport(value("report_date"));
    (document.getElementById("rendered_report") as HTMLTextAreaElement).value = String(data.rendered_text || "");
  }

  async loadReport() {
    const data = await this.api.getReport(value("report_date"));
    (document.getElementById("rendered_report") as HTMLTextAreaElement).value = String(data.rendered_text || "");
  }

  async sendTelegram() {
    await this.api.sendTelegram(value("report_date"));
  }

  async saveTelegram() {
    await this.api.saveTelegram({
      enabled: (document.getElementById("tg_enabled") as HTMLInputElement).checked,
      bot_token: value("tg_bot_token") || undefined,
      admin_chat_id: value("tg_chat_id") || undefined,
      admin_username: value("tg_username")
    });
  }

  reportText() {
    return (document.getElementById("rendered_report") as HTMLTextAreaElement | null)?.value || "";
  }

  humanError(err: unknown) {
    return err instanceof Error ? err.message : "Неизвестная ошибка";
  }
}

function check(key: string, checked: boolean) {
  return `<div><input type="checkbox" data-event-key="${key}" ${checked ? "checked" : ""}></div>`;
}

function value(id: string): string {
  return (document.getElementById(id) as HTMLInputElement | null)?.value || "";
}

function numberValue(id: string): number {
  return Number(value(id));
}

function bootstrap() {
  const root = document.getElementById("amo-control-widget") || document.body.appendChild(document.createElement("div"));
  root.id = "amo-control-widget";
  void new App().mount(root);
}

bootstrap();
