from phoenix.toolbox.logger.logger import Logger


def test_logger_write_and_reset_hooks_are_used():
    writes = []
    resets = []

    logger = Logger(filename=None, stdout=False)
    logger.set_logfile(
        "hooked.log",
        path=".",
        reset=True,
        write_hook=lambda lines: writes.append(list(lines)),
        reset_hook=lambda lines: resets.append(list(lines)),
    )
    logger.info("hello", source="test")

    assert resets
    assert any("LOGFILE" in line for line in resets[0])
    assert len(writes) == 1
    assert len(writes[0]) == 1
    assert writes[0][0].endswith("info @test         | hello")


def test_controlled_restores_alert_state_after_exception():
    logger = Logger(filename=None, stdout=False)

    @logger.controlled
    def fail():
        raise RuntimeError("boom")

    assert logger._alerted is True
    try:
        fail()
    except RuntimeError:
        pass

    assert logger._alerted is True
