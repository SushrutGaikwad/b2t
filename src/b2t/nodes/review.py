from langgraph.types import interrupt
from loguru import logger

from b2t.state import PipelineState


def _approve(state: PipelineState) -> dict:
    """Commit the candidate frame and advance to the next."""
    return {
        "converted_frames": [*state.converted_frames, state.candidate],
        "frame_index": state.frame_index + 1,
        "candidate": None,
        "feedback": None,
    }


def review_node(state: PipelineState) -> dict:
    """Approve or regenerate the candidate frame.

    Without HITL, auto-approves. With HITL, pauses on an interrupt carrying the
    review payload and resumes on the reviewer's decision: approve commits and
    advances; regenerate stores feedback and leaves the frame in place so the
    convert node re-runs it.
    """
    if not state.hitl_enabled:
        return _approve(state)
    decision = interrupt(
        {
            "frame_index": state.frame_index,
            "total": len(state.frames),
            "candidate": state.candidate,
            "preview_ok": state.preview_pdf is not None and state.preview_error is None,
            "preview_error": state.preview_error,
        }
    )
    if decision.get("action") == "approve":
        return _approve(state)
    logger.debug("regenerate frame {}", state.frame_index + 1)
    return {"feedback": decision.get("feedback"), "candidate": None}
