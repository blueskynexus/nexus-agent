"""Rules table widget displaying rule status and statistics."""

import httpx
from fastapi import HTTPException

from registry import register_widget
from src.config import settings


@register_widget(
    {
        "name": "Rules",
        "description": "Display rules with status and statistics",
        "category": "Rules",
        "type": "table",
        "endpoint": "rules",
        "gridData": {"w": 20, "h": 10},
        "refetchInterval": 60000,
        "data": {
            "table": {
                "columnsDefs": [
                    {
                        "field": "id",
                        "headerName": "ID",
                        "cellDataType": "text",
                        "width": 280,
                        "hide": True,
                    },
                    {
                        "field": "name",
                        "headerName": "Name",
                        "cellDataType": "text",
                        "width": 280,
                    },
                    {
                        "field": "isActive",
                        "headerName": "Active",
                        "cellDataType": "boolean",
                        "width": 100,
                        "renderFn": "greenRed",
                    },
                    {
                        "field": "ran",
                        "headerName": "Ran",
                        "cellDataType": "number",
                        "formatterFn": "int",
                        "width": 100,
                    },
                    {
                        "field": "passed",
                        "headerName": "Passed",
                        "cellDataType": "number",
                        "formatterFn": "int",
                        "width": 100,
                        "renderFn": "greenRed",
                    },
                    {
                        "field": "failed",
                        "headerName": "Failed",
                        "cellDataType": "number",
                        "formatterFn": "int",
                        "width": 100,
                        "renderFn": "greenRed",
                    },
                    {
                        "field": "dateCreated",
                        "headerName": "Created",
                        "cellDataType": "text",
                        "width": 120,
                        "hide": True,
                    },
                    {
                        "field": "dateUpdated",
                        "headerName": "Updated",
                        "cellDataType": "text",
                        "width": 120,
                        "hide": True,
                    },
                    {
                        "field": "lastPassed",
                        "headerName": "Last Passed",
                        "cellDataType": "number",
                        "width": 140,
                        "hide": True,
                    },
                    {
                        "field": "lastFailed",
                        "headerName": "Last Failed",
                        "cellDataType": "number",
                        "width": 140,
                        "hide": True,
                    },
                ]
            }
        },
    }
)
def get_rules():
    """Fetch and return all rules from the API.

    Returns:
        list: List of rule objects with status and statistics.

    Raises:
        HTTPException: If the API request fails.
    """
    url = f"{settings.vianexus_base_url}/rules"
    params = {"token": settings.vianexus_api_key}

    response = httpx.get(url, params=params, timeout=10)

    if response.status_code != 200:
        raise HTTPException(
            status_code=response.status_code,
            detail=f"Failed to fetch rules: {response.text}",
        )

    return response.json()
