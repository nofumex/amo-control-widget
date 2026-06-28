from __future__ import annotations

from collections import defaultdict

from app.reports.metrics import format_duration
from app.reports.schemas import ReportSnapshotPayload


def render_telegram_report(snapshot: ReportSnapshotPayload) -> str:
    lines = [f"📊 Отчет по активности менеджеров за {snapshot.report_date.strftime('%d.%m.%Y')}", ""]
    if not snapshot.users:
        lines.append("Сотрудники для отчета не выбраны.")
        return "\n".join(lines)

    groups: dict[str, list] = defaultdict(list)
    for row in sorted(snapshot.users, key=lambda item: (item.group.lower(), item.name.lower())):
        groups[row.group].append(row)

    for group, users in groups.items():
        lines.append(f"Группа: {group}")
        lines.append("")
        for index, row in enumerate(users, start=1):
            first = row.first_activity_at or "-"
            last = row.last_activity_at or "-"
            lines.extend(
                [
                    f"{index}. {row.name}",
                    f"   ⏱ Непрерывная работа: {format_duration(row.continuous_work_seconds)}",
                    f"   ✅ Задач выполнено: {row.completed_tasks_count}",
                    f"   ☎️ Входящие: {row.incoming_calls_count}",
                    f"   📞 Исходящие: {row.outgoing_calls_count}",
                    f"   📝 Примечания: {row.notes_count}",
                    f"   ⚠️ Просрочено задач: {row.overdue_tasks_count}",
                    f"   🕘 Первая активность: {first}",
                    f"   🕕 Последняя активность: {last}",
                    "",
                ]
            )
    return "\n".join(lines).strip()
