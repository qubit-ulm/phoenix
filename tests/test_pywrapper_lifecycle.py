import gc
import weakref

from phoenix.fgen.backends.pywrapper_library import (
    PyWrapperLibraryBase,
    WrapperBase,
)


class DummyOwner:
    def __init__(self):
        self.released_tokens = []

    def release_wrapper(self, token):
        self.released_tokens.append(token)


def test_wrapper_releases_owner_token_on_collection():
    owner = DummyOwner()
    wrapper = WrapperBase(
        name="demo",
        exe=lambda *_args: None,
        arguments=[],
        owner=owner,
        owner_token=7,
    )

    del wrapper
    gc.collect()

    assert owner.released_tokens == [7]


def test_pywrapper_library_auto_closes_after_last_wrapper_is_collected():
    library = object.__new__(PyWrapperLibraryBase)
    library._wrappers = weakref.WeakValueDictionary()
    library._wrapper_names_by_token = {}
    library._wrapper_tokens_by_name = {}
    library._wrapper_lib = object()
    library._next_wrapper_token = 0
    library._closed = False
    library._close_finalizer = None

    wrapper = WrapperBase(
        name="demo",
        exe=lambda *_args: None,
        arguments=[],
        owner=library,
        owner_token=3,
    )
    library.register_wrapper("demo", 3, wrapper)

    del wrapper
    gc.collect()

    assert library._closed is True
    assert library._wrapper_lib is None


def test_pywrapper_library_get_wrapper_uses_name_without_clashing_with_tokens():
    library = object.__new__(PyWrapperLibraryBase)
    library._wrappers = weakref.WeakValueDictionary()
    library._wrapper_names_by_token = {}
    library._wrapper_tokens_by_name = {}
    library._wrapper_lib = object()
    library._next_wrapper_token = 0
    library._closed = False
    library._close_finalizer = None

    first = WrapperBase(
        name="demo",
        exe=lambda *_args: None,
        arguments=[],
        owner=library,
        owner_token=1,
    )
    second = WrapperBase(
        name="demo",
        exe=lambda *_args: None,
        arguments=[],
        owner=library,
        owner_token=2,
    )
    other = WrapperBase(
        name="other",
        exe=lambda *_args: None,
        arguments=[],
        owner=library,
        owner_token=4,
    )
    library.register_wrapper("demo", 1, first)
    library.register_wrapper("demo", 2, second)
    library.register_wrapper("other", 4, other)

    assert library.get_wrapper("demo") is second
    assert library.get_wrapper("other") is other
