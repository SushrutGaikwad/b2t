from b2t.llm import ConverterLLM, FakeConverter


def test_fake_converter_returns_canned_output():
    fake = FakeConverter("= Typst\n")
    assert fake.convert(latex_source="x", reference="y") == "= Typst\n"


def test_fake_converter_satisfies_protocol():
    fake = FakeConverter()
    assert isinstance(fake, ConverterLLM)
