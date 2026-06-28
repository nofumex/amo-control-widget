export function telegramPage(settings: Record<string, unknown>): string {
  return `
    <label class="acw-check"><input id="tg_enabled" type="checkbox" ${settings.enabled ? "checked" : ""}> Включить доставку</label>
    <div class="acw-grid">
      <label><span>Bot token</span><input id="tg_bot_token" type="password" placeholder="${settings.bot_token_masked || ""}"></label>
      <label><span>Admin chat id</span><input id="tg_chat_id" type="password" placeholder="${settings.admin_chat_id_masked || ""}"></label>
      <label><span>Admin username</span><input id="tg_username" value="${settings.admin_username || ""}"></label>
      <label><span>Последний тест</span><input readonly value="${settings.last_test_status || "-"}"></label>
    </div>
    <button class="acw-primary" data-action="save-telegram">Сохранить</button>
    <button data-action="test-telegram">Отправить тест</button>
  `;
}
