from evals.adapters.stream_parser import parse_stream


def test_agent_trace_event_parsed_as_meta():
    chunks = [
        'data: {"type":"agent-trace","traceId":"trace-1","role":"retrieval_agent","stage":"handoff","status":"ok","latencyMs":7}\n\n',
        'data: {"type":"finish","finishReason":"stop"}\n\n',
        "data: [DONE]\n\n",
    ]
    parsed = parse_stream(chunks)
    kinds = [e.kind for e in parsed.events]
    assert "meta" in kinds
    assert "done" in kinds
