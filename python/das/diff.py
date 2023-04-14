from argparse import ArgumentError
from dataclasses import dataclass
import deepdiff
from deepdiff.operator import BaseOperator
from enum import Enum
from typing import Any, List, Optional, TYPE_CHECKING
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
    def iterable_items_added(self):
        return Diff.DiffPath.list_from_deepdiff(self._deepdiff.get('iterable_item_added')),

    @property
    def iterable_items_removed(self):
        return Diff.DiffPath.list_from_deepdiff(self._deepdiff.get('iterable_item_removed')),

    @property
    def affected_paths(self):
        return Diff.DiffPath.list_from_deepdiff(self._deepdiff.affected_paths)

    @property
    def unaffected_paths(self):
        return Diff.DiffPath.list_from_deepdiff(self._deepdiff.get('same'))


class Same(BaseOperator):
    def __init__(self, regex_paths: Optional[List[str]] = None):
        if not regex_paths:
            regex_paths = ['.*']
        super().__init__(regex_paths)

    def give_up_diffing(self, level, diff_instance):
        if level.t1 == level.t2:
            diff_instance.custom_report_result('same', level, {})
            return True
        return False


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
    difference = deepdiff.DeepDiff(dict(base), dict(other), view='tree', custom_operators=[Same()])

    return Diff(_deepdiff=difference, type_comparison_result=type_comparison)

def _extract_path(base, intersection, path):
    intersection_path = str(path[0])
    if len(path) == 1:
        intersection[intersection_path] = base[path[0]]
    else:
        if intersection_path not in intersection:
            intersection[intersection_path] = {}

        # TODO remove recursion
        _extract_path(base[path[0]], intersection[intersection_path], path[1:])

def get_intersection(base, other: Optional[Struct] = None, diff: Optional[Diff] = None, preserve_list: bool = False):
    if diff is None:
        if other is None:
            raise ArgumentError('other or diff is required')
        diff = diff(base, other)

    unaffected_paths = diff.unaffected_paths
    intersection = Struct()
    for path in unaffected_paths:
        _extract_path(base, intersection, path.path)

    return intersection
