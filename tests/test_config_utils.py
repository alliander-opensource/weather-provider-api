#!/usr/bin/env python
# -*- coding: utf-8 -*-

# SPDX-FileCopyrightText: 2019-2021 Alliander N.V.
#
# SPDX-License-Identifier: MPL-2.0

from wpla.config.utils.config_utils import build_config


def test__extend_config_dict():
    # Case #1: No overlap
    dummy_base_config = {
        'item_one': "output_one",
        'item_two': "output_two"
    }
    dummy_extending_config = {
        'item_three': "output_three"
    }

    # No overlap means extending the base_config to three items
    extended_config = build_config(dummy_base_config, dummy_extending_config)
    assert len(extended_config) == 3
    assert 'item_three' in extended_config

    # Case #2: Full overlap
    dummy_base_config = {
        'item_one': "output_one",
        'item_two': "output_two"
    }
    dummy_extending_config = {
        'item_one': "output_one_extra"
    }

    # The full overlap means the base_config still should have two items, one of which was overwritten
    extended_config = build_config(dummy_base_config, dummy_extending_config)
    assert len(extended_config) == 2
    assert extended_config['item_one'] == 'output_one_extra'

    # Case #3: Partial Overlap
    dummy_base_config = {
        'item_one': "output_one",
        'item_two': "output_two"
    }
    dummy_extending_config = {
        'item_one': "output_one_extra",
        'item_three': "output_three"
    }

    # The partial overlap means the base_config still should have three items, one of which was overwritten
    extended_config = build_config(dummy_base_config, dummy_extending_config)
    assert len(extended_config) == 3
    assert extended_config['item_one'] == 'output_one_extra'

    # Case #4: Sub-levels
    dummy_base_config = {
        'item_one': {
            'sub_item_one': 'sub_output_one'
        }
    }
    dummy_extending_config = {
        'item_one': {
            'sub_item_one': 'sub_output_one_extra'
        }
    }

    # The item on the sublevel should be rewritten as per the extending config
    extended_config = build_config(dummy_base_config, dummy_extending_config)
    print(extended_config)
    assert len(extended_config) == 1
    assert extended_config['item_one']['sub_item_one'] == 'sub_output_one_extra'

    # Case #5: Sub-sub-levels
    dummy_base_config = {
        'item_one': {
            'sub_item_one': {
                'sub_sub_item_one': 'sub_sub_output_one'
            }
        }
    }
    dummy_extending_config = {
        'item_one': {
            'sub_item_one': {
                'sub_sub_item_one': 'sub_sub_output_one_extra'
            }
        }
    }

    # The item on the sublevel should be rewritten as per the extending config
    extended_config = build_config(dummy_base_config, dummy_extending_config)
    print(extended_config)
    assert len(extended_config) == 1
    assert extended_config['item_one']['sub_item_one']['sub_sub_item_one'] == 'sub_sub_output_one_extra'

    # Case #6: Complexity (Everything put together)
    dummy_base_config = {
        'item_one': {
            'sub_item_one': {
                'sub_sub_item_one': 'sub_sub_output_one'
            },
            'sub_item_two': 'sub_output_two'
        },
        'item_two': 'output_two'
    }

    dummy_extending_config = {
        'item_one': {
            'sub_item_one': {
                'sub_sub_item_one': 'sub_sub_output_one_extra'
            }
        },
        'item_two': {
            'sub_item_two': 'sub_output_two'
        },
        'item_three': 'output_three'
    }

    # The following should happen:
    # - 'sub_sub_item_one' should be rewritten
    # - 'item_two' should be rewritten from a value into a sub-item list
    # - 'item_three' should be appended
    extended_config = build_config(dummy_base_config, dummy_extending_config)
    print(extended_config)
    assert len(extended_config) == 3
    assert extended_config['item_one']['sub_item_one']['sub_sub_item_one'] == 'sub_sub_output_one_extra'
    assert 'sub_item_two' in extended_config['item_two']
    assert 'item_three' in extended_config
