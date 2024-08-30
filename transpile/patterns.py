
def any_character_except(these: list[str]):
    return rf"[^{"".join(these)}]"

