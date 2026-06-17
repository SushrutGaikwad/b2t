from pathlib import Path

from b2t.config import DEFAULT_MODEL
from b2t.llm import FakeClient
from b2t.nodes._llm import run_prompt
from b2t.state import NodeChoice, NodeRun, PipelineState


def _state(**kwargs) -> PipelineState:
    base = {"input_dir": Path("in"), "output_dir": Path("out")}
    base.update(kwargs)
    return PipelineState(**base)


# Superset of tokens across convert prompt versions; render ignores keys a
# given template does not reference, so this works for v1/v2 (source) and v3
# (preamble, frame).
_VALUES = {
    "reference": "R",
    "guides": "G",
    "source": "SRC",
    "aspect_ratio": "4-3",
    "preamble": "PRE",
    "frame": "FRAMEBODY",
}


def test_run_prompt_uses_defaults_and_returns_run(monkeypatch):
    monkeypatch.delenv("B2T_MODEL", raising=False)
    out, run, rendered = run_prompt(_state(), "convert", FakeClient("OUT"), _VALUES)
    assert out == "OUT"
    assert run == NodeRun(model=DEFAULT_MODEL, prompt_version="v3")
    assert "FRAMEBODY" in rendered.user
    assert rendered.system


def test_run_prompt_honors_choice_model_and_renders_user(monkeypatch):
    monkeypatch.delenv("B2T_MODEL", raising=False)
    state = _state(llm_choices={"convert": NodeChoice(model="x/y", prompt_version="v1")})
    captured = {}

    class Spy:
        def complete(self, system, user, model):
            captured["model"] = model
            captured["user"] = user
            return "OK"

    out, run, rendered = run_prompt(state, "convert", Spy(), _VALUES)
    assert captured["model"] == "x/y"
    assert "SRC" in captured["user"]
    assert run.model == "x/y"
    assert run.prompt_version == "v1"
    assert rendered.user == captured["user"]


def test_run_prompt_falls_back_to_b2t_model_env(monkeypatch):
    monkeypatch.setenv("B2T_MODEL", "env/model")
    _, run, _ = run_prompt(_state(), "convert", FakeClient("OUT"), _VALUES)
    assert run.model == "env/model"
