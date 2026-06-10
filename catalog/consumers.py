import json

from channels.db import database_sync_to_async
from channels.generic.websocket import AsyncWebsocketConsumer
from django.template.loader import render_to_string

from .models import ChecklistItem

GROUP = "checklist"  # alle verbundenen Tabs landen in dieser Gruppe


class ChecklistConsumer(AsyncWebsocketConsumer):
    """Server-Seite der Echtzeit-Checkliste (asynchron).

    Ablauf bei einem Toggle:
    1. Ein Tab sendet {"action": "toggle", "id": ...} ueber den WebSocket.
    2. Wir aendern den Datensatz in der DB (einzige Quelle der Wahrheit).
    3. Wir rendern die Zeile als HTML-Fragment und schicken es an die GANZE
       Gruppe. HTMX tauscht das Fragment per Out-of-Band-Swap in jeden Tab ein.

    Async-Variante: Channel-Layer-Aufrufe werden direkt ge-await-et. Nur der
    blockierende DB-Zugriff laeuft ueber database_sync_to_async in einem Thread.
    """

    async def connect(self):
        await self.channel_layer.group_add(GROUP, self.channel_name)
        await self.accept()

    async def disconnect(self, code):
        await self.channel_layer.group_discard(GROUP, self.channel_name)

    async def receive(self, text_data):
        data = json.loads(text_data)
        if data.get("action") != "toggle":
            return

        html = await self.toggle_and_render(data["id"])
        await self.channel_layer.group_send(
            GROUP, {"type": "checklist_update", "html": html}
        )

    # Wird fuer jeden in der Gruppe aufgerufen (Name = "type" oben mit _ statt .).
    async def checklist_update(self, event):
        await self.send(text_data=event["html"])

    @database_sync_to_async
    def toggle_and_render(self, item_id):
        # Laeuft im Thread: hier ist normaler, synchroner ORM-Zugriff erlaubt.
        item = ChecklistItem.objects.get(pk=item_id)
        item.done = not item.done
        item.save()
        return render_to_string(
            "catalog/_checklist_item.html", {"item": item, "oob": True}
        )
