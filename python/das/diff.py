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
    _deepdiff: deepdiff.DeepDiff

    @property
    def types_changed(self):
        return Diff.DiffPath.list_from_deepdiff(self._deepdiff.get('type_changes')),

    @property
    def values_changed(self):
        return Diff.DiffPath.list_from_deepdiff(self._deepdiff.get('values_changed')),

    @property
    def items_added(self):
        return Diff.DiffPath.list_from_deepdiff(self._deepdiff.get('dictionary_item_added')),

    @property
    def items_removed(self):
        return Diff.DiffPath.list_from_deepdiff(self._deepdiff.get('dictionary_item_removed')),

    @property
    def affected_paths(self):
        return Diff.DiffPath.list_from_deepdiff(self._deepdiff.affected_paths)



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

    return Diff(_deepdiff=difference, type_comparison_result=type_comparison)
