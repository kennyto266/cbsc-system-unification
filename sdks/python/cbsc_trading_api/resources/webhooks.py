"""
Webhooks resource for CBSC Trading API SDK
"""

from typing import Optional, List, Dict, Any
from ..models import Webhook, WebhookCreate, WebhookEventType, APIResponse
from ..client import CBSCClient


class WebhooksResource:
    """Resource for webhook management operations"""

    def __init__(self, client: CBSCClient):
        self.client = client

    def get_webhooks(self, skip: int = 0, limit: int = 100) -> APIResponse:
        """
        Get list of webhooks with pagination

        Args:
            skip: Number of webhooks to skip
            limit: Maximum number of webhooks to return

        Returns:
            APIResponse: List of webhooks
        """
        params = {"skip": skip, "limit": limit}
        response = self.client.get("/api/v1/webhooks/", params=params)
        response_data = response.json()

        # Convert webhook data to Webhook objects if needed
        if isinstance(response_data.get("data"), list):
            webhooks = [Webhook(**webhook_data) for webhook_data in response_data["data"]]
            response_data["data"] = webhooks

        return APIResponse(**response_data)

    def get_webhook(self, webhook_id: int) -> Webhook:
        """
        Get webhook by ID

        Args:
            webhook_id: Webhook ID

        Returns:
            Webhook: Webhook information
        """
        response = self.client.get(f"/api/v1/webhooks/{webhook_id}")
        response_data = response.json()

        return Webhook(**response_data)

    def create_webhook(self, webhook_data: WebhookCreate) -> Webhook:
        """
        Create a new webhook

        Args:
            webhook_data: Webhook creation data

        Returns:
            Webhook: Created webhook information
        """
        # Convert enum values to strings
        data = webhook_data.dict(exclude_none=True)
        if "events" in data:
            data["events"] = [event.value if isinstance(event, WebhookEventType) else event
                            for event in data["events"]]

        response = self.client.post("/api/v1/webhooks/", data=data)
        response_data = response.json()

        return Webhook(**response_data)

    def update_webhook(self, webhook_id: int, webhook_data: dict) -> Webhook:
        """
        Update webhook information

        Args:
            webhook_id: Webhook ID
            webhook_data: Updated webhook data

        Returns:
            Webhook: Updated webhook information
        """
        # Convert enum values to strings if present
        if "events" in webhook_data:
            webhook_data["events"] = [event.value if isinstance(event, WebhookEventType) else event
                                    for event in webhook_data["events"]]

        response = self.client.put(f"/api/v1/webhooks/{webhook_id}", data=webhook_data)
        response_data = response.json()

        return Webhook(**response_data)

    def delete_webhook(self, webhook_id: int) -> bool:
        """
        Delete a webhook

        Args:
            webhook_id: Webhook ID

        Returns:
            bool: True if deletion successful
        """
        response = self.client.delete(f"/api/v1/webhooks/{webhook_id}")
        return response.status_code == 200

    def test_webhook(self, webhook_id: int, test_data: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Test a webhook endpoint

        Args:
            webhook_id: Webhook ID
            test_data: Optional test data to send

        Returns:
            Dict: Test results
        """
        data = test_data or {"test": True}
        response = self.client.post(f"/api/v1/webhooks/{webhook_id}/test", data=data)
        return response.json()

    def get_webhook_stats(self, webhook_id: int) -> Dict[str, Any]:
        """
        Get webhook delivery statistics

        Args:
            webhook_id: Webhook ID

        Returns:
            Dict: Webhook statistics
        """
        response = self.client.get(f"/api/v1/webhooks/{webhook_id}/stats")
        return response.json()

    def get_webhook_deliveries(self, webhook_id: int, skip: int = 0, limit: int = 50) -> List[Dict[str, Any]]:
        """
        Get webhook delivery history

        Args:
            webhook_id: Webhook ID
            skip: Number of deliveries to skip
            limit: Maximum number of deliveries to return

        Returns:
            List[Dict]: List of webhook deliveries
        """
        params = {"skip": skip, "limit": limit}
        response = self.client.get(f"/api/v1/webhooks/{webhook_id}/deliveries", params=params)
        response_data = response.json()

        if isinstance(response_data.get("data"), list):
            return response_data["data"]
        else:
            return [response_data]

    def retry_webhook_delivery(self, webhook_id: int, delivery_id: int) -> Dict[str, Any]:
        """
        Retry a failed webhook delivery

        Args:
            webhook_id: Webhook ID
            delivery_id: Delivery ID

        Returns:
            Dict: Retry results
        """
        response = self.client.post(f"/api/v1/webhooks/{webhook_id}/retry/{delivery_id}")
        return response.json()

    def get_available_events(self) -> List[WebhookEventType]:
        """
        Get list of available webhook event types

        Returns:
            List[WebhookEventType]: Available event types
        """
        response = self.client.get("/api/v1/webhooks/events")
        response_data = response.json()

        events = []
        if isinstance(response_data.get("data"), list):
            for event in response_data["data"]:
                try:
                    events.append(WebhookEventType(event))
                except ValueError:
                    # Skip unknown event types
                    pass

        return events

    def trigger_event(self, event_type: WebhookEventType, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Manually trigger a webhook event

        Args:
            event_type: Event type to trigger
            data: Event data

        Returns:
            Dict: Trigger results
        """
        trigger_data = {
            "event": event_type.value,
            "data": data,
        }
        response = self.client.post("/api/v1/webhooks/events/trigger", data=trigger_data)
        return response.json()