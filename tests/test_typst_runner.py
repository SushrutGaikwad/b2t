import pytest

from b2t.typst_runner import compile_typst, typst_available

pytestmark = pytest.mark.integration


def test_missing_typst_cli_records_clear_error(tmp_path, monkeypatch):
    def raise_missing(*args, **kwargs):
        raise FileNotFoundError("typst")

    monkeypatch.setattr("b2t.typst_runner.subprocess.run", raise_missing)
    typ = tmp_path / "any.typ"
    typ.write_text("= Hi\n", encoding="utf-8")
    result = compile_typst(typ)
    assert not result.ok
    assert "typst CLI not found" in result.error


@pytest.mark.skipif(not typst_available(), reason="typst binary not installed")
def test_compile_success(tmp_path):
    typ = tmp_path / "ok.typ"
    typ.write_text("= Hello\n\nWorld\n", encoding="utf-8")
    result = compile_typst(typ)
    assert result.ok
    assert result.pdf_path is not None and result.pdf_path.exists()


@pytest.mark.skipif(not typst_available(), reason="typst binary not installed")
def test_compile_failure_records_error(tmp_path):
    typ = tmp_path / "bad.typ"
    typ.write_text("#this_is_not_defined()\n", encoding="utf-8")
    result = compile_typst(typ)
    assert not result.ok
    assert result.error
