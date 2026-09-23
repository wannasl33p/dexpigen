"""Tests for the piping module (systems, segments, connections)."""

import pytest
from pydantic import ValidationError

from dexpigen.equipment import Nozzle
from dexpigen.piping import (
    Pipe,
    PipingConnection,
    PipingNetworkSegment,
    PipingNetworkSegmentItem,
    PipingNetworkSystem,
    PipingNode,
    PipingNodeOwner,
    PipingSourceItem,
    PipingTargetItem,
)


def test_connection_is_abstract():
    with pytest.raises(TypeError):
        PipingConnection(dex_id="C-1")


def test_roles_are_abstract():
    for cls in (
        PipingNodeOwner,
        PipingSourceItem,
        PipingTargetItem,
        PipingNetworkSegmentItem,
    ):
        with pytest.raises(TypeError):
            cls(dex_id="x")


def test_pipe_is_concrete():
    pipe = Pipe(dex_id="pipe-1")
    assert isinstance(pipe, PipingConnection)
    assert isinstance(pipe.id, str)


def test_system_composes_segments():
    segment = PipingNetworkSegment(dex_id="seg-1")
    system = PipingNetworkSystem(dex_id="S-1", segments=[segment])
    assert system.segments[0] is segment


def test_add_segment_composes_under_system():
    system = PipingNetworkSystem(dex_id="S-1")
    segment = PipingNetworkSegment(dex_id="seg-1")
    assert system.add_segment(segment) is system
    assert segment in system.segments


def test_segment_cannot_have_two_owners():
    sys_a = PipingNetworkSystem(dex_id="S-1")
    sys_b = PipingNetworkSystem(dex_id="S-2")
    segment = PipingNetworkSegment(dex_id="seg-1")
    sys_a.add_segment(segment)
    with pytest.raises(ValueError):
        sys_b.add_segment(segment)


def test_connection_cannot_have_two_owners():
    seg_a = PipingNetworkSegment(dex_id="seg-1")
    seg_b = PipingNetworkSegment(dex_id="seg-2")
    pipe = Pipe(dex_id="pipe-1")
    seg_a.add_connection(pipe)
    with pytest.raises(ValueError):
        seg_b.add_connection(pipe)


def test_line_number_is_optional():
    system = PipingNetworkSystem(dex_id="S-1")
    assert system.line_number is None
    named = PipingNetworkSystem(dex_id="S-2", line_number="100-P-1")
    assert named.line_number == "100-P-1"


def test_nozzle_is_a_valid_piping_source_and_target():
    nozzle = Nozzle(dex_id="N-1")
    source_pipe = Pipe(dex_id="p-1", source_item=nozzle)
    assert source_pipe.source_item is nozzle
    target_pipe = Pipe(dex_id="p-2", target_item=nozzle)
    assert target_pipe.target_item is nozzle


def test_connection_node_must_belong_to_its_item():
    nozzle = Nozzle(dex_id="N-1")
    node = PipingNode(dex_id="node-1")
    nozzle.add_node(node)
    Pipe(dex_id="p-1", source_item=nozzle, source_node=node)


def test_connection_node_rejects_foreign_node():
    nozzle = Nozzle(dex_id="N-1")
    node = PipingNode(dex_id="node-1")  # not added to the nozzle
    with pytest.raises(ValidationError):
        Pipe(dex_id="p-1", source_item=nozzle, source_node=node)


def test_connection_node_without_item_is_rejected():
    node = PipingNode(dex_id="node-1")
    with pytest.raises(ValidationError):
        Pipe(dex_id="p-1", source_node=node)


def test_node_cannot_have_two_owners():
    nozzle_a = Nozzle(dex_id="N-1")
    nozzle_b = Nozzle(dex_id="N-2")
    node = PipingNode(dex_id="node-1")
    nozzle_a.add_node(node)
    with pytest.raises(ValueError):
        nozzle_b.add_node(node)
