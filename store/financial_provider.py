"""Proveedor determinista B-03D. No incluye cliente HTTP ni credenciales Stripe."""

from dataclasses import dataclass
from datetime import datetime


class SimulatedProviderUnavailable(Exception):
    pass


@dataclass(frozen=True)
class ProviderSession:
    id: str
    account_id: str
    environment: str
    created: datetime
    status: str
    payment_status: str
    mode: str
    payment_intent_id: str
    amount_total: int
    currency: str
    client_reference_id: str
    amount_discount: int = 0
    amount_tax: int = 0
    amount_shipping: int = 0


@dataclass(frozen=True)
class ProviderIntent:
    id: str
    account_id: str
    environment: str
    created: datetime
    status: str
    capture_method: str
    amount: int
    amount_received: int
    currency: str


@dataclass(frozen=True)
class ProviderLine:
    price_id: str
    product_id: str
    quantity: int
    amount_total: int
    currency: str


@dataclass(frozen=True)
class ProviderEvent:
    id: str
    account_id: str
    environment: str
    type: str
    object_id: str
    created: datetime


class SimulatedFinancialProvider:
    """Fixture inmutable por identidad; los fallos se inyectan explícitamente."""

    def __init__(self, *, account_id, environment, sessions, intents, lines, events):
        self.account_id = account_id
        self.environment = environment
        self.sessions = dict(sessions)
        self.intents = dict(intents)
        self.lines = {key: tuple(value) for key, value in lines.items()}
        self.events = dict(events)
        self.fail_next = False
        self.calls = []

    def _get(self, collection, key, operation):
        self.calls.append((operation, key))
        if self.fail_next:
            self.fail_next = False
            raise SimulatedProviderUnavailable('provider_temporarily_unavailable')
        return collection[key]

    def get_session(self, session_id):
        return self._get(self.sessions, session_id, 'session')

    def get_intent(self, intent_id):
        return self._get(self.intents, intent_id, 'intent')

    def get_all_lines(self, session_id):
        return self._get(self.lines, session_id, 'all_lines')

    def find_success_events(self, intent_id):
        self.calls.append(('success_events', intent_id))
        if self.fail_next:
            self.fail_next = False
            raise SimulatedProviderUnavailable('provider_temporarily_unavailable')
        return tuple(event for event in self.events.values()
                     if event.type == 'payment_intent.succeeded' and event.object_id == intent_id)
