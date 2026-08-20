raise ImportError(
    "services.orchestrator.celery_entrypoint was removed - use "
    "services.gateway.turn_processor.process_turn_and_dispatch instead. "
    "See that module's docstring for why."
)
