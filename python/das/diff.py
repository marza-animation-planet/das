from dataclasses import dataclass
import deepdiff
from enum import Enum
from typing import Any, List, TYPE_CHECKING

if TYPE_CHECKING:
    from .types import Struct

class TypeComparisonResult(int, Enum):
    SAME=0
    BASE_SUBCLASS_OF_OTHER=1
    OTHER_SUBCLASS_OF_BASE=2
    DIFFERENT=3


@dataclass
class Diff:
    @dataclass
    class DiffPath:
        path: List[str]

        @classmethod
        def list_from_deepdiff(cls, deepdiff_result):
            if not deepdiff_result:
                return []
            results = [cls(path=level.path(output_format='list')) for level in deepdiff_result]
            return results

    type_comparison_result: TypeComparisonResult
    types_changed: List[DiffPath]
    values_changed: List[DiffPath]
    items_added: List[DiffPath]
    items_removed: List[DiffPath]
    affected_paths: List[DiffPath]


def compare_types(base: Any, other: Any) -> TypeComparisonResult:
    base_type = type(base)
    other_type = type(other)
    if base_type == other_type:
        return TypeComparisonResult.SAME
    elif issubclass(base_type, other_type):
        return TypeComparisonResult.BASE_SUBCLASS_OF_OTHER
    elif issubclass(base_type, other_type):
        return TypeComparisonResult.OTHER_SUBCLASS_OF_BASE
    else:
        return TypeComparisonResult.DIFFERENT

def diff(base: 'Struct', other: 'Struct', diff_different_types=False, diff_subclasses=True) -> Diff:
    type_comparison = compare_types(base, other)
    if type_comparison == TypeComparisonResult.DIFFERENT and not diff_different_types:
        return type_comparison, None
    if type_comparison in [TypeComparisonResult.BASE_SUBCLASS_OF_OTHER, TypeComparisonResult.OTHER_SUBCLASS_OF_BASE] and \
        not diff_subclasses:
        return type_comparison, None
    difference = deepdiff.DeepDiff(dict(base), dict(other), view='tree')

    return Diff(
        type_comparison_result=type_comparison,
        types_changed=Diff.DiffPath.list_from_deepdiff(difference.get('type_changes')),
        values_changed=Diff.DiffPath.list_from_deepdiff(difference.get('values_changed')),
        items_added=Diff.DiffPath.list_from_deepdiff(difference.get('dictionary_item_added')),
        items_removed=Diff.DiffPath.list_from_deepdiff(difference.get('dictionary_item_removed')),
        affected_paths=Diff.DiffPath.list_from_deepdiff(difference.affected_paths)
    )

def delta(base: 'Struct', other: 'Struct', diff_different_types=False, diff_subclasses=True):
    pass

def get_unaffected(base, diff):
    pass