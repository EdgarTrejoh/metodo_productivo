"""Contrato interno de Checkout; esta implementación nunca usa la red."""

from dataclasses import dataclass
from datetime import timedelta
from django.utils import timezone


class ProviderUncertain(Exception):
    """La solicitud pudo haberse aplicado antes de perderse la respuesta."""


@dataclass(frozen=True)
class PriceQuote:
    price_id: str
    product_id: str
    amount_minor: int
    currency: str
    account_id: str
    environment: str
    active: bool = True
    recurring: bool = False


@dataclass(frozen=True)
class CheckoutSession:
    session_id: str
    url: str
    status: str
    expires_at: object
    account_id: str
    environment: str


class SimulatedCheckoutProvider:
    """Estado determinista para pruebas; no acepta credenciales ni tiene cliente HTTP."""

    def __init__(self, *, prices, account_id, environment):
        self.prices = dict(prices)
        self.account_id = account_id
        self.environment = environment
        self.sessions = {}
        self.lost_response_once = False
        self.create_calls = 0
        self.last_request = None

    def get_price(self, price_id):
        return self.prices[price_id]

    def create_session(self, *, idempotency_key, price_id, quantity, mode,
                       success_url, cancel_url, client_reference_id, operation_id,
                       payment_method_types):
        self.last_request = dict(price_id=price_id, quantity=quantity, mode=mode,
            success_url=success_url, cancel_url=cancel_url,
            client_reference_id=client_reference_id,
            payment_method_types=payment_method_types)
        if idempotency_key not in self.sessions:
            self.create_calls += 1
            session = CheckoutSession(
                session_id=f'cs_test_{operation_id.hex}',
                url=f'https://checkout.example.invalid/{operation_id.hex}',
                status='open', expires_at=timezone.now() + timedelta(hours=1),
                account_id=self.account_id, environment=self.environment,
            )
            self.sessions[idempotency_key] = session
        if self.lost_response_once:
            self.lost_response_once = False
            raise ProviderUncertain('La respuesta de creación se perdió.')
        return self.sessions[idempotency_key]

    def get_session(self, *, idempotency_key, session_id=None, expected=None):
        session = self.sessions.get(idempotency_key)
        return session if session_id is None or (session and session.session_id == session_id) else None
