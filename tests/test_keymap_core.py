from __future__ import annotations

import pytest

from phoenix.keymap import Entry, Key, KeyMap, Region


def make_nested_keymap():
    scalar = KeyMap(name="scalar")
    scalar.entry("real")
    scalar.entry("imag")

    vector = KeyMap(name="vector")
    vector.link("x", scalar)
    vector.link("y", scalar)
    return scalar, vector


def test_keymap_key_roundtrip_and_recursive_keys():
    scalar, vector = make_nested_keymap()

    key = vector.key("x")
    assert key.labels == ("x",)
    assert key.parents == (vector,)
    assert vector.key2off(Key("x"), Key("imag")) == 1
    assert vector.off2key(2).labels == ("y", "real")
    assert [item.labels for item in vector.keys(recursive=True)] == [
        ("x", "real"),
        ("x", "imag"),
        ("y", "real"),
        ("y", "imag"),
    ]
    assert vector.key2dom("y") is scalar


def test_keymap_extend_autorenames_duplicate_domain_names():
    root = KeyMap(name="root")
    root.extend(Entry(name="node"))
    root.extend(Entry(name="node"))

    assert "node" in root
    assert "node.2" in root
    assert list(key.labels[0] for key in root.keys()) == ["node", "node.2"]


def test_keymap_label_keys_and_items_stay_tagged():
    scalar, vector = make_nested_keymap()

    items = list(vector.items())

    assert items[0][0].labels == ("x",)
    assert items[0][0].parents == (vector,)
    assert items[0][1] is scalar


def test_keymap_lock_prevents_mutation():
    keymap = KeyMap(name="locked")
    keymap.entry("a")
    keymap.lock()

    with pytest.raises(ValueError):
        keymap.entry("b")

    with pytest.raises(ValueError):
        keymap.extend(Entry(name="c"))


def test_region_auto_entries_use_integer_indices():
    region = Region(3, name="grid")

    assert region.size == 3
    assert [key.labels[0] for key in region.keys()] == [0, 1, 2]
    assert region.off2key(1).labels == (1,)


def test_keymap_contains_and_getitem_accept_labels_and_keys():
    scalar, vector = make_nested_keymap()

    assert "x" in vector
    assert Key("y") in vector
    assert vector["x"] is scalar
    assert vector[Key("y")] is scalar
