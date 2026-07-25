import pytest

from services.orchestrator import celery_entrypoint


class _FakeGraph:
    async def ainvoke(self, state_update, config):
        assert state_update["whatsapp_number"] == "919876543210"
        assert config["configurable"]["thread_id"] == "919876543210"
        return {
            "outbound_messages": [
                {"type": "text", "body": "ঠিক আছে"},
                {"type": "document", "url": "https://example.com/report.pdf", "filename": "report.pdf", "caption": "রিপোর্ট"},
                {"type": "image", "url": "https://example.com/poster.jpg", "caption": "পোস্টার"},
            ]
        }


@pytest.mark.asyncio
async def test_process_turn_delivers_graph_outbound_messages(monkeypatch):
    sent = []

    async def _graph():
        return _FakeGraph()

    async def _send_text(to, body):
        sent.append(("text", to, body))
        return {"messages": [{"id": "text-id"}]}

    async def _send_document(to, url, filename, caption=""):
        sent.append(("document", to, url, filename, caption))
        return {"messages": [{"id": "doc-id"}]}

    async def _send_image(to, url, caption=""):
        sent.append(("image", to, url, caption))
        return {"messages": [{"id": "image-id"}]}

    monkeypatch.setattr(celery_entrypoint, "get_compiled_graph", _graph)
    monkeypatch.setattr(celery_entrypoint, "send_text", _send_text)

    import shared.whatsapp.sender as sender

    monkeypatch.setattr(sender, "send_document", _send_document)
    monkeypatch.setattr(sender, "send_image", _send_image)

    await celery_entrypoint._process_turn_async("919876543210", {"raw_input_text": "hello"})

    assert sent == [
        ("text", "919876543210", "ঠিক আছে"),
        ("document", "919876543210", "https://example.com/report.pdf", "report.pdf", "রিপোর্ট"),
        ("image", "919876543210", "https://example.com/poster.jpg", "পোস্টার"),
    ]
