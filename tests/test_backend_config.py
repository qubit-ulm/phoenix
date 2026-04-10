from phoenix.fgen.backend_config import Configuration


def test_configuration_dot_paths_roundtrip():
    config = Configuration.empty("demo")
    config.set_path("fortran.omp.num_cores", 8)
    config.set_path(("fortran", "enabled"), True)

    assert config.get_path("fortran.omp.num_cores") == 8
    assert config.get_path("fortran.enabled") is True
    assert config.has_path("fortran.omp.num_cores")
    assert sorted(config.iter_paths()) == [
        (("fortran", "enabled"), True),
        (("fortran", "omp", "num_cores"), 8),
    ]
