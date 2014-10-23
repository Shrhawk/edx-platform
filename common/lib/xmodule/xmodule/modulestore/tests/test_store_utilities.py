"""
Tests for store_utilities.py
"""
import unittest
from mock import Mock
import ddt

from xmodule.modulestore.store_utilities import (
    get_subtree_roots_from_draft_nodes, draft_node_constructor
)


def mock_location(category):
    """
    Helper function to generate a mock location with a parameter-specified
    category attribute.
    """
    mock_parent_location = Mock()
    mock_parent_location.category = category
    return mock_parent_location


@ddt.ddt
class TestUtils(unittest.TestCase):
    """
    Tests for store_utilities

    ASCII trees for ONLY_ROOTS and SOME_TREES:

    ONLY_ROOTS:
    1)
        vertical
          |
        url1

    2)
        sequential
          |
        url2

    SOME_TREES:

    1)
            sequential_1
                 |
            vertical_1
              /     \
             /       \
        child_1    child_2

    2)
        chapter_1
           |
        sequential_1

    3)
        great_grandparent_vertical
                    |
            grandparent_vertical
                    |
                vertical_2
                 /      \
                /        \
            child_3    child_4
    """

    ONLY_ROOTS = [
        draft_node_constructor(Mock(), 'url1', 'vertical', parent_location=mock_location('vertical')),
        draft_node_constructor(Mock(), 'url2', 'sequential', parent_location=mock_location('sequential')),
    ]
    ONLY_ROOTS_URLS = ['url1', 'url2']

    SOME_TREES = [
        draft_node_constructor(Mock(), 'child_1', 'vertical_1', parent_location=mock_location('vertical')),
        draft_node_constructor(Mock(), 'child_2', 'vertical_1', parent_location=mock_location('vertical')),
        draft_node_constructor(Mock(), 'vertical_1', 'sequential_1', parent_location=mock_location('sequential')),

        # NOTE: it is not actually possible for sequentials to be drafts
        # However, in this test we add a sequential to the draft tree in order
        # to check that, when using locations, get_subtree_roots_from_draft_nodes automatically
        # yields any node whose parent is a sequential.
        draft_node_constructor(Mock(), 'sequential_1', 'chapter_1', parent_location=mock_location('chapter')),

        draft_node_constructor(Mock(), 'child_3', 'vertical_2', parent_location=mock_location('vertical')),
        draft_node_constructor(Mock(), 'child_4', 'vertical_2', parent_location=mock_location('vertical')),
        draft_node_constructor(Mock(), 'vertical_2', 'grandparent_vertical', parent_location=mock_location('vertical')),
        draft_node_constructor(Mock(), 'grandparent_vertical', 'great_grandparent_vertical', parent_location=mock_location('vertical')),
    ]

    SOME_TREES_ROOTS_URLS_WITHOUT_LOCATIONS = ['sequential_1', 'grandparent_vertical']
    # when using locations, we should also yield vertical_1, whose parent is a sequential node
    SOME_TREES_ROOTS_URLS_WITH_LOCATIONS = ['vertical_1', 'sequential_1', 'grandparent_vertical']

    @ddt.data(
        (ONLY_ROOTS, ONLY_ROOTS_URLS, False),
        (ONLY_ROOTS, ONLY_ROOTS_URLS, True),
        (SOME_TREES, SOME_TREES_ROOTS_URLS_WITHOUT_LOCATIONS, False),
        (SOME_TREES, SOME_TREES_ROOTS_URLS_WITH_LOCATIONS, True),
    )
    @ddt.unpack
    def test_get_subtree_roots_from_draft_nodes(self, module_nodes, expected_roots_urls, use_locations):
        """tests for get_subtree_roots_from_draft_nodes"""
        subtree_roots_urls = [root.url for root in get_subtree_roots_from_draft_nodes(module_nodes, use_locations)]
        # make sure each root url is distinct
        self.assertEqual(len(subtree_roots_urls), len(set(subtree_roots_urls)))
        # make sure each expected url is distinct
        self.assertEqual(len(expected_roots_urls), len(set(expected_roots_urls)))
        # check that we return the expected urls
        self.assertEqual(set(subtree_roots_urls), set(expected_roots_urls))
