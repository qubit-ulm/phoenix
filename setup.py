from setuptools import find_packages, setup

setup(
    name="phoenix",
    version="1.0",
    description="Parallel Hybrid Operations for Enhanced Numerical Implementations and eXecutions",
    author="Matthias Kost",
    author_email="matthias.kost@uni-ulm.de",
    packages=find_packages(),
    include_package_data=True,
    package_data={
        "phoenix.fgen.backends": ["config/general.json", "basic_coeffops.c"],
        "phoenix.fgen.backends.c": [
            "c_default.json",
            "support/Makefile",
            "support/include/*",
            "support/src/*",
        ],
        "phoenix.fgen.backends.fortran": [
            "fortran_default.json",
            "support/Makefile",
        ],
        "phoenix.fgen.backends.cuda": [
            "cuda_default.json",
            "support/Makefile",
            "support/include/*",
            "support/src/*",
        ],
        "phoenix.fgen.backends.opencl": [
            "opencl_default.json",
            "support/Makefile",
        ],
        "phoenix.fgen.backends.python": [
            "python_default.json",
            "support/Makefile",
        ],
        "phoenix.fgen.backends.numpy": [
            "numpy_default.json",
            "support/Makefile",
        ],
        "phoenix.fgen.backends.plain": [
            "plain_default.json",
            "support/Makefile",
        ],
        "phoenix.fgen.backends.julia": [
            "julia_default.json",
            "support/Makefile",
        ],
        "phoenix.fgen.backends.matlab": [
            "matlab_default.json",
            "support/Makefile",
        ],
    },
    install_requires=["numpy"],
    extras_require={
        "docs": ["sphinx-rtd-theme"],
        "test": ["pytest"],
        "opencl": ["pyopencl"],
        "cuda-cupy": ["cupy"],
        "cuda-pycuda": ["pycuda"],
        "dev": ["pytest", "sphinx-rtd-theme"],
    },
    scripts=[
        "bin/phoenix-config",
        "bin/phoenix-config-gui",
        "bin/phoenix-config-init",
    ],
)
