import pytest

from phoenix.keymap import Entry, Key, KeyMap


def test_link_with_none_domain_creates_entry():
    """link(key, None) should create a leaf Entry at the given key."""
    keymap = KeyMap(name="base")

    returned = keymap.link("alpha", None)

    assert returned is keymap
    assert "alpha" in keymap
    assert keymap.size == 1
    assert isinstance(keymap.key2dom("alpha"), Entry)
    assert keymap.key2off("alpha") == 0
    assert keymap.off2key(0).labels == ("alpha",)


def test_link_with_explicit_domain_keeps_domain_identity_and_size():
    """link(key, domain) should attach the exact domain object."""
    keymap = KeyMap(name="base")
    domain = KeyMap(name="domain")
    domain.entry("leaf_0")
    domain.entry("leaf_1")

    keymap.link("domain", domain)

    assert keymap.key2dom("domain") is domain
    assert keymap.size == 2
    assert keymap.key2off("domain") == 0
    assert keymap.key2off("domain", "leaf_0") == 0
    assert keymap.key2off("domain", "leaf_1") == 1


def test_link_rejects_duplicate_key_by_default():
    """link should protect existing keys when no_override=True."""
    keymap = KeyMap(name="base")
    keymap.link("alpha", None)

    with pytest.raises(KeyError, match="already exists"):
        keymap.link("alpha", None)


def test_link_nested_keymap_with_multisegment_key_from_base():
    """
    A multi-segment key passed to the base keymap should traverse into the
    nested keymap and link the new domain there.
    """
    base = KeyMap(name="base")
    nested = KeyMap(name="nested")

    # Seed the nested keymap so resolving base["nested"] during link traversal
    # does not force an update of an empty child keymap.
    nested.entry("existing")
    base.link("nested", nested)

    returned = base.link(
        Key("nested") | Key("linked_from_base"), Entry(name="some inner entry")
    )

    assert returned is base
    assert "linked_from_base" in nested
    assert isinstance(nested.key2dom("linked_from_base"), Entry)
    assert base.key2dom("nested", "linked_from_base") is nested.key2dom(
        "linked_from_base"
    )
    assert base.key2off("nested", "existing") == 0
    assert base.key2off("nested", "linked_from_base") == 1
    assert base.off2key(1).labels == ("nested", "linked_from_base")


def test_link_nested_keymap_with_tagged_multisegment_key():
    """The same nested link operation should work with tagged key segments."""
    base = KeyMap(name="base")
    nested = KeyMap(name="nested")
    nested.entry("existing")
    base.link("nested", nested)

    tagged_path = base.key("nested") | nested.key("linked_with_tags")
    base.link(tagged_path, None)

    assert "linked_with_tags" in nested
    assert isinstance(base.key2dom("nested", "linked_with_tags"), Entry)
    assert base.off2key(1).labels == ("nested", "linked_with_tags")
