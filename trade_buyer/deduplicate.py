"""Merge exact normalized names within a country and dataset type."""
from dataclasses import replace
from .models import Buyer


def deduplicate(buyers: list[Buyer]) -> tuple[list[Buyer], int]:
    groups = {}
    duplicates = 0
    for buyer in buyers:
        key = (buyer.normalized_name, buyer.country.casefold(), buyer.sources[0].record_type)
        if key not in groups:
            groups[key] = replace(buyer, materials=set(buyer.materials), sources=list(buyer.sources))
            continue
        duplicates += 1
        target = groups[key]
        target.materials.update(buyer.materials)
        if len(target.materials) > 1:
            target.materials.discard("unclassified")
        for source in buyer.sources:
            if source not in target.sources:
                target.sources.append(source)
    return list(groups.values()), duplicates
