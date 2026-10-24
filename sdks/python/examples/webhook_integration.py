"""
Webhook integration example for CBSC Trading API Python SDK
"""

from cbsc_trading_api import CBSCClient
from cbsc_trading_api.models import WebhookCreate, WebhookEventType

def main():
    """Webhook integration example"""

    client = CBSCClient(
        base_url="http://localhost:3005",
        client_id="test_client_id",
        client_secret="test_client_secret"
    )

    try:
        print("=== Webhook Integration Example ===\n")

        # 1. Get available webhook events
        print("1. Getting available webhook events...")
        try:
            events = client.webhooks.get_available_events()
            print("   Available events:")
            for event in events:
                print(f"     - {event.value}")
        except Exception as e:
            print(f"   Error getting events: {e}")
            events = list(WebhookEventType)  # Fallback to enum values
        print()

        # 2. Create a new webhook
        print("2. Creating new webhook...")
        webhook_data = WebhookCreate(
            url="https://example.com/webhook/cbsc-events",
            events=[
                WebhookEventType.STRATEGY_CREATED,
                WebhookEventType.STRATEGY_UPDATED,
                WebhookEventType.ORDER_FILLED,
                WebhookEventType.PORTFOLIO_UPDATED,
            ],
            description="Webhook for monitoring strategy and portfolio events",
            is_active=True,
            secret="my_webhook_secret_123"
        )

        try:
            new_webhook = client.webhooks.create_webhook(webhook_data)
            print(f"   Created webhook: {new_webhook.url} (ID: {new_webhook.id})")
            print(f"   Events: {[e.value for e in new_webhook.events]}")
            webhook_id = new_webhook.id
        except Exception as e:
            print(f"   Error creating webhook: {e}")
            # Use existing webhook for demo
            webhooks = client.webhooks.get_webhooks(limit=1)
            if webhooks.data:
                webhook_id = webhooks.data[0].id
                print(f"   Using existing webhook ID: {webhook_id}")
            else:
                print("   No webhooks available")
                return
        print()

        # 3. Get webhook details
        print("3. Getting webhook details...")
        webhook = client.webhooks.get_webhook(webhook_id)
        print(f"   Webhook URL: {webhook.url}")
        print(f"   Description: {webhook.description}")
        print(f"   Active: {webhook.is_active}")
        print(f"   Created at: {webhook.created_at}")
        print(f"   Events: {[e.value for e in webhook.events]}")
        print()

        # 4. Test webhook
        print("4. Testing webhook...")
        try:
            test_result = client.webhooks.test_webhook(
                webhook_id,
                test_data={
                    "event": "test",
                    "message": "This is a test webhook",
                    "timestamp": "2024-01-01T00:00:00Z"
                }
            )
            print(f"   Test result: {test_result}")
        except Exception as e:
            print(f"   Error testing webhook: {e}")
        print()

        # 5. Get webhook statistics
        print("5. Getting webhook statistics...")
        try:
            stats = client.webhooks.get_webhook_stats(webhook_id)
            print(f"   Webhook stats: {stats}")
        except Exception as e:
            print(f"   Error getting stats: {e}")
        print()

        # 6. Get webhook delivery history
        print("6. Getting webhook delivery history...")
        try:
            deliveries = client.webhooks.get_webhook_deliveries(webhook_id, limit=5)
            print(f"   Recent deliveries: {len(deliveries)}")
            for delivery in deliveries[:3]:  # Show first 3
                print(f"     - ID: {delivery.get('id')}, Status: {delivery.get('status')}")
        except Exception as e:
            print(f"   Error getting deliveries: {e}")
        print()

        # 7. Trigger a manual event
        print("7. Triggering manual webhook event...")
        try:
            trigger_result = client.webhooks.trigger_event(
                WebhookEventType.STRATEGY_CREATED,
                {
                    "strategy_id": 123,
                    "strategy_name": "Test Strategy",
                    "created_by": "user@example.com"
                }
            )
            print(f"   Trigger result: {trigger_result}")
        except Exception as e:
            print(f"   Error triggering event: {e}")
        print()

        # 8. Update webhook
        print("8. Updating webhook...")
        try:
            update_data = {
                "description": "Updated webhook description",
                "is_active": False  # Temporarily disable
            }
            updated_webhook = client.webhooks.update_webhook(webhook_id, update_data)
            print(f"   Updated description: {updated_webhook.description}")
            print(f"   Active status: {updated_webhook.is_active}")
        except Exception as e:
            print(f"   Error updating webhook: {e}")
        print()

        print("=== Webhook Integration Example Completed ===")

    except Exception as e:
        print(f"Error: {e}")
    finally:
        client.close()

if __name__ == "__main__":
    main()