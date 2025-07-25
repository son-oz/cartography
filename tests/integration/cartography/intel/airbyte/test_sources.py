from unittest.mock import Mock
from unittest.mock import patch

import cartography.intel.airbyte.sources
import tests.data.airbyte.sources
import tests.data.airbyte.workspaces
from tests.integration.cartography.intel.airbyte.test_organizations import (
    _ensure_local_neo4j_has_test_organizations,
)
from tests.integration.cartography.intel.airbyte.test_workspaces import (
    _ensure_local_neo4j_has_test_workspaces,
)
from tests.integration.util import check_nodes
from tests.integration.util import check_rels

TEST_UPDATE_TAG = 123456789
TEST_ORG_ID = "31634962-4b3c-4b0c-810d-a2a77d6df222"


def _ensure_local_neo4j_has_test_sources(neo4j_session):
    cartography.intel.airbyte.sources.load_sources(
        neo4j_session,
        tests.data.airbyte.sources.AIRBYTE_SOURCES,
        TEST_ORG_ID,
        TEST_UPDATE_TAG,
    )


@patch.object(
    cartography.intel.airbyte.sources,
    "get",
    return_value=tests.data.airbyte.sources.AIRBYTE_SOURCES,
)
def test_load_airbyte_sources(mock_api, neo4j_session):
    """
    Ensure that sources actually get loaded
    """

    # Arrange
    api_session = Mock()
    common_job_parameters = {
        "UPDATE_TAG": TEST_UPDATE_TAG,
        "ORG_ID": TEST_ORG_ID,
    }
    workspace_ids = [
        w["workspaceId"] for w in tests.data.airbyte.workspaces.AIRBYTE_WORKSPACES
    ]
    _ensure_local_neo4j_has_test_workspaces(neo4j_session)
    _ensure_local_neo4j_has_test_organizations(neo4j_session)

    # Act
    cartography.intel.airbyte.sources.sync(
        neo4j_session,
        api_session,
        TEST_ORG_ID,
        workspace_ids,
        common_job_parameters,
    )

    # Assert Sources exist
    expected_nodes = {
        (
            "b626221b-9250-4c8b-8615-653ca7e807ab",
            "Postgres",
            "postgres",
            "localho.st",
            1234,
            "springfield",
        ),
    }
    assert (
        check_nodes(
            neo4j_session,
            "AirbyteSource",
            ["id", "name", "type", "config_host", "config_port", "config_name"],
        )
        == expected_nodes
    )

    # Assert Sources are connected to the organization
    expected_rels = {
        ("b626221b-9250-4c8b-8615-653ca7e807ab", TEST_ORG_ID),
    }
    assert (
        check_rels(
            neo4j_session,
            "AirbyteSource",
            "id",
            "AirbyteOrganization",
            "id",
            "RESOURCE",
            rel_direction_right=False,
        )
        == expected_rels
    )

    # Assert sources are connected to the workspace
    expected_rels = {
        (
            "e4388e31-9c21-461b-9b5d-1905ca28c599",
            "b626221b-9250-4c8b-8615-653ca7e807ab",
        ),
    }
    assert (
        check_rels(
            neo4j_session,
            "AirbyteWorkspace",
            "id",
            "AirbyteSource",
            "id",
            "CONTAINS",
            rel_direction_right=True,
        )
        == expected_rels
    )
