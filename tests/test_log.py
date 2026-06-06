from loguru import logger

from b2t.log import setup_logging


def test_setup_logging_writes_to_rotating_file(tmp_path):
    setup_logging(tmp_path)
    logger.info("hello from the test")
    logger.complete()
    log_file = tmp_path / "b2t.log"
    assert log_file.exists()
    assert "hello from the test" in log_file.read_text(encoding="utf-8")


def test_setup_logging_is_repeatable(tmp_path):
    setup_logging(tmp_path)
    setup_logging(tmp_path)
    logger.info("logged once")
    logger.complete()
    content = (tmp_path / "b2t.log").read_text(encoding="utf-8")
    assert content.count("logged once") == 1
