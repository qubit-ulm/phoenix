# The Keymap Module

The keymap module introduces tree-like datastructures to support the design of complex  and highly specific datatypes. Within a keymap, entries are accessed via keys, which can be composed from any hashable object such as strings, numbers or tuples of them. As a rule of thumb, anything that could work as a key in a python dictionary can translate into a key as well.

To simplify the access in complex multi-layered keymaps, multiple keys can be chained into a single multi-segment key.

Keys can be tagged to assign them to a keymap. When the tag on a tagged key does not match the keymap, an exception is thrown to avoid misaddressing.

A Region is a subclass of the Keymap. A region has a fixed length and its keys are simply enumerated. It can only contain entries and allows for no further hierarchy.

An Entry is a subclass of a Region. It has length one and cannot contain anything else.

