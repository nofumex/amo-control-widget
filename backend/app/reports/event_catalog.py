from __future__ import annotations

from typing import Literal

from pydantic import BaseModel

EventSource = Literal["events_api", "tasks_api", "notes_api", "webhook", "digital_pipeline"]


class EventCatalogItem(BaseModel):
    code: str
    title_ru: str
    title_en: str
    description_ru: str
    default_enabled_as_activity: bool = False
    default_enabled_as_counter: bool = False
    default_enabled_as_penalty: bool = False
    requires_note_lookup: bool = False
    supports_stage_filter: bool = False
    source: EventSource = "events_api"


EVENT_CATALOG: tuple[EventCatalogItem, ...] = (
    EventCatalogItem(
        code="task_completed",
        title_ru="Задача выполнена",
        title_en="Task completed",
        description_ru="Событие завершения задачи пользователем.",
        default_enabled_as_activity=True,
        default_enabled_as_counter=True,
    ),
    EventCatalogItem(
        code="task_deadline_changed",
        title_ru="Срок задачи изменен",
        title_en="Task deadline changed",
        description_ru="Перенос срока задачи. По умолчанию считается счетчиком, а не активностью.",
        default_enabled_as_counter=True,
        default_enabled_as_penalty=True,
    ),
    EventCatalogItem(
        code="common_note_added",
        title_ru="Примечание добавлено",
        title_en="Common note added",
        description_ru="Обычное примечание в карточке.",
        default_enabled_as_activity=True,
        default_enabled_as_counter=True,
    ),
    EventCatalogItem(
        code="incoming_call",
        title_ru="Входящий звонок",
        title_en="Incoming call",
        description_ru="Входящий звонок, длительность берется из params.duration примечания.",
        default_enabled_as_activity=True,
        default_enabled_as_counter=True,
        requires_note_lookup=True,
        source="notes_api",
    ),
    EventCatalogItem(
        code="outgoing_call",
        title_ru="Исходящий звонок",
        title_en="Outgoing call",
        description_ru="Исходящий звонок, длительность берется из params.duration примечания.",
        default_enabled_as_activity=True,
        default_enabled_as_counter=True,
        requires_note_lookup=True,
        source="notes_api",
    ),
    EventCatalogItem(
        code="lead_status_changed",
        title_ru="Сделка перешла этап",
        title_en="Lead status changed",
        description_ru="Переход сделки между этапами. Поддерживает фильтры pipeline/status.",
        default_enabled_as_counter=True,
        supports_stage_filter=True,
    ),
    EventCatalogItem(code="entity_responsible_changed", title_ru="Ответственный изменен", title_en="Responsible user changed", description_ru="Смена ответственного в сущности.", default_enabled_as_counter=True),
    EventCatalogItem(code="lead_created", title_ru="Сделка создана", title_en="Lead created", description_ru="Создание сделки.", default_enabled_as_counter=True),
    EventCatalogItem(code="lead_deleted", title_ru="Сделка удалена", title_en="Lead deleted", description_ru="Удаление сделки.", default_enabled_as_penalty=True),
    EventCatalogItem(code="contact_created", title_ru="Контакт создан", title_en="Contact created", description_ru="Создание контакта.", default_enabled_as_counter=True),
    EventCatalogItem(code="company_created", title_ru="Компания создана", title_en="Company created", description_ru="Создание компании.", default_enabled_as_counter=True),
    EventCatalogItem(code="customer_created", title_ru="Покупатель создан", title_en="Customer created", description_ru="Создание покупателя.", default_enabled_as_counter=True),
    EventCatalogItem(code="incoming_chat_message", title_ru="Входящее сообщение", title_en="Incoming chat message", description_ru="Входящее сообщение чата.", default_enabled_as_counter=True),
    EventCatalogItem(code="outgoing_chat_message", title_ru="Исходящее сообщение", title_en="Outgoing chat message", description_ru="Исходящее сообщение чата.", default_enabled_as_activity=True, default_enabled_as_counter=True),
    EventCatalogItem(code="incoming_sms", title_ru="Входящее SMS", title_en="Incoming SMS", description_ru="Входящее SMS.", default_enabled_as_counter=True),
    EventCatalogItem(code="outgoing_sms", title_ru="Исходящее SMS", title_en="Outgoing SMS", description_ru="Исходящее SMS.", default_enabled_as_activity=True, default_enabled_as_counter=True),
    EventCatalogItem(code="entity_linked", title_ru="Связь добавлена", title_en="Entity linked", description_ru="Связь между сущностями добавлена.", default_enabled_as_counter=True),
    EventCatalogItem(code="entity_unlinked", title_ru="Связь удалена", title_en="Entity unlinked", description_ru="Связь между сущностями удалена.", default_enabled_as_counter=True),
    EventCatalogItem(code="custom_field_value_changed", title_ru="Поле изменено", title_en="Custom field changed", description_ru="Изменение значения пользовательского поля.", default_enabled_as_counter=True),
)


def default_event_map(attribute: str) -> dict[str, bool]:
    return {item.code: bool(getattr(item, attribute)) for item in EVENT_CATALOG}
