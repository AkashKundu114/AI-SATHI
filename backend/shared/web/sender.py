async def send_text(to_number: str, text: str) -> None:
    pass

async def send_image(to_number: str, url: str, caption: str = "") -> None:
    pass

async def send_document(to_number: str, url: str, filename: str, caption: str = "") -> None:
    pass

async def send_flow(to_number: str, flow_id: str, flow_token: str, payload: dict, fallback_text: str) -> None:
    pass
