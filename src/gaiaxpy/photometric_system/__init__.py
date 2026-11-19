"""Define photometric systems and manage the available filter selection.

The public PhotometricSystem registry exposes built-in systems and any loaded
additional systems through attributes, including interactive tab completion.
Additional systems have release and version identifiers, such as
USER_DR3_Example_v1. Loading a new selection replaces the previous additional
systems while keeping the same registry object.
"""
