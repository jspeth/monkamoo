def join_strings(items, conj="and"):
    """Return a string by joining the items with the conjunction."""
    items = list(items)
    if len(items) == 1:
        return items[0]
    if len(items) == 2:
        return f"{items[0]} {conj} {items[1]}"
    return "{list}, {conj} {last}".format(list=", ".join(items[:-1]), last=items[-1], conj=conj)
