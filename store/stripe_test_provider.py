"""Adaptador Stripe TEST. Su activación interna está deshabilitada por defecto."""

import os
import uuid
from collections.abc import Mapping
from dataclasses import dataclass
from datetime import datetime, timezone as dt_timezone
from threading import Lock
from urllib.parse import urlsplit

import stripe
from django.conf import settings
from django.utils import timezone

from store.checkout_provider import PriceQuote, ProviderUncertain
from store.financial_provider import (ProviderEvent, ProviderIntent, ProviderLine,
                                      ProviderUnavailable)


class StripeProviderDataError(ValueError):
    """La respuesta no satisface el contrato; nunca exponer el cuerpo original."""


def _value(obj, name):
    return obj.get(name) if isinstance(obj, Mapping) else getattr(obj, name, None)


def _text(obj, name):
    value = _value(obj, name)
    if not isinstance(value, str) or not value:
        raise StripeProviderDataError('provider_object_incomplete')
    return value


def _integer(obj, name, *, positive=False):
    value = _value(obj, name)
    if type(value) is not int or value < (1 if positive else 0):
        raise StripeProviderDataError('provider_object_incomplete')
    return value


def _time(obj, name):
    value = _integer(obj, name, positive=True)
    try:
        return datetime.fromtimestamp(value, tz=dt_timezone.utc)
    except (ValueError, OSError, OverflowError) as exc:
        raise StripeProviderDataError('provider_time_invalid') from exc


def _id(value):
    if isinstance(value, str):
        return value
    return _value(value, 'id') or ''


def _test_object(obj):
    if _value(obj, 'livemode') is not False:
        raise StripeProviderDataError('provider_environment_mismatch')


@dataclass(frozen=True)
class StripeTestSession:
    id: str
    url: str
    status: str
    expires_at: datetime
    account_id: str
    environment: str
    created: datetime
    payment_status: str
    mode: str
    payment_intent_id: str
    amount_total: int
    currency: str
    client_reference_id: str
    amount_discount: int
    amount_tax: int
    amount_shipping: int

    @property
    def session_id(self):
        return self.id


class StripeTestProvider:
    """Normaliza objetos del SDK; no tiene ruta pública ni concede derechos."""

    environment = 'test'

    def __init__(self, *, client, account_id):
        if not account_id.startswith('acct_') or not client:
            raise StripeProviderDataError('invalid_test_configuration')
        self._client = client
        self.account_id = account_id
        self._verified_account = False
        self._account_lock = Lock()
        self._quotes = {}
        self._intents = {}

    @classmethod
    def from_environment(cls):
        """Solo la configuración interna explícita puede construir el cliente real."""
        if not settings.STRIPE_TEST_ADAPTER_ENABLED:
            raise StripeProviderDataError('stripe_test_adapter_disabled')
        key = os.environ.get('STRIPE_TEST_RESTRICTED_KEY', '')
        account_id = os.environ.get('STRIPE_TEST_ACCOUNT_ID', '')
        if not key.startswith('rk_test_') or len(key) < 16:
            raise StripeProviderDataError('invalid_test_key_configuration')
        return cls(client=stripe.StripeClient(key, max_network_retries=0),
                   account_id=account_id)

    def _enabled(self):
        if not settings.STRIPE_TEST_ADAPTER_ENABLED:
            raise StripeProviderDataError('stripe_test_adapter_disabled')

    def _call(self, method, *args, creation=False, **kwargs):
        try:
            return method(*args, **kwargs)
        except stripe.StripeError as exc:
            if creation:
                raise ProviderUncertain('stripe_create_outcome_uncertain') from exc
            if isinstance(exc, (stripe.APIConnectionError, stripe.APIError,
                                stripe.RateLimitError, stripe.IdempotencyError)):
                raise ProviderUnavailable('stripe_temporarily_unavailable') from exc
            raise StripeProviderDataError('stripe_request_rejected') from exc

    def _account(self):
        self._enabled()
        if self._verified_account:
            return
        with self._account_lock:
            if self._verified_account:
                return
            account = self._call(self._client.v1.accounts.retrieve_current)
            if _text(account, 'id') != self.account_id:
                raise StripeProviderDataError('provider_account_mismatch')
            if _value(account, 'livemode') is True:
                raise StripeProviderDataError('provider_environment_mismatch')
            self._verified_account = True

    def get_price(self, price_id):
        self._account()
        if not isinstance(price_id, str) or not price_id.startswith('price_'):
            raise StripeProviderDataError('invalid_price_id')
        raw = self._call(self._client.v1.prices.retrieve, price_id)
        _test_object(raw)
        if (_text(raw, 'id') != price_id or _value(raw, 'active') is not True
                or _value(raw, 'recurring') is not None
                or _value(raw, 'type') != 'one_time'
                or _value(raw, 'billing_scheme') != 'per_unit'
                or _value(raw, 'custom_unit_amount') is not None
                or _value(raw, 'transform_quantity') is not None
                or _text(raw, 'currency').upper() != 'MXN'):
            raise StripeProviderDataError('provider_price_mismatch')
        product_id = _id(_value(raw, 'product'))
        if not product_id.startswith('prod_'):
            raise StripeProviderDataError('provider_product_missing')
        quote = PriceQuote(price_id, product_id, _integer(raw, 'unit_amount', positive=True),
                           'MXN', self.account_id, 'test')
        self._quotes[price_id] = quote
        return quote

    def _session(self, raw, *, expected=None):
        _test_object(raw)
        session_id = _text(raw, 'id')
        if not session_id.startswith('cs_test_'):
            raise StripeProviderDataError('provider_session_identity')
        details = _value(raw, 'total_details')
        tax = _value(raw, 'automatic_tax')
        methods = _value(raw, 'payment_method_types')
        if (details is None or tax is None or _value(tax, 'enabled') is not False
                or methods != ['card'] or _value(raw, 'allow_promotion_codes') is True
                or _value(_value(raw, 'adaptive_pricing'), 'enabled') is True):
            raise StripeProviderDataError('provider_session_terms')
        url = _value(raw, 'url') or ''
        status = _text(raw, 'status')
        if status == 'open':
            parsed = urlsplit(url)
            if (parsed.scheme != 'https' or parsed.hostname != 'checkout.stripe.com'
                    or _value(raw, 'payment_status') != 'unpaid'):
                raise StripeProviderDataError('provider_checkout_url')
        session = StripeTestSession(
            id=session_id, url=url, status=status,
            expires_at=_time(raw, 'expires_at'), account_id=self.account_id,
            environment='test', created=_time(raw, 'created'),
            payment_status=_text(raw, 'payment_status'),
            mode=_text(raw, 'mode'),
            payment_intent_id=_id(_value(raw, 'payment_intent')),
            amount_total=_integer(raw, 'amount_total', positive=True),
            currency=_text(raw, 'currency').upper(),
            client_reference_id=_text(raw, 'client_reference_id'),
            amount_discount=_integer(details, 'amount_discount'),
            amount_tax=_integer(details, 'amount_tax'),
            amount_shipping=_integer(details, 'amount_shipping'),
        )
        if (session.expires_at <= session.created or session.mode != 'payment'
                or session.currency != 'MXN'
                or any((session.amount_discount, session.amount_tax,
                        session.amount_shipping))):
            raise StripeProviderDataError('provider_session_mismatch')
        if expected:
            quote = self._quotes.get(expected['price_id'])
            if (quote is None or session.amount_total != quote.amount_minor
                    or session.client_reference_id != expected['client_reference_id']
                    or _value(raw, 'success_url') != expected['success_url']
                    or _value(raw, 'cancel_url') != expected['cancel_url']
                    or _value(_value(raw, 'metadata'), 'operation_id') !=
                    str(expected['operation_id'])):
                raise StripeProviderDataError('provider_session_mismatch')
        return session

    def get_session(self, session_id=None, *, idempotency_key=None, expected=None):
        self._account()
        if session_id is None:
            # Stripe no ofrece GET por idempotency key.
            return None
        if not isinstance(session_id, str) or not session_id.startswith('cs_test_'):
            raise StripeProviderDataError('provider_session_identity')
        raw = self._call(self._client.v1.checkout.sessions.retrieve, session_id)
        session = self._session(raw, expected=expected)
        if session.id != session_id:
            raise StripeProviderDataError('provider_session_identity')
        return session

    def create_session(self, *, idempotency_key, price_id, quantity, mode,
                       success_url, cancel_url, client_reference_id, operation_id,
                       payment_method_types):
        self._account()
        if (not isinstance(operation_id, uuid.UUID)
                or not isinstance(idempotency_key, str)
                or not isinstance(quantity, int) or quantity != 1
                or mode != 'payment' or payment_method_types != ('card',)
                or price_id not in self._quotes):
            raise StripeProviderDataError('provider_create_parameters')
        params = {
            'mode': 'payment',
            'line_items': [{'price': price_id, 'quantity': 1}],
            'success_url': success_url,
            'cancel_url': cancel_url,
            'client_reference_id': client_reference_id,
            'metadata': {'operation_id': str(operation_id)},
            'payment_intent_data': {'metadata': {'operation_id': str(operation_id)}},
            'allowed_payment_method_types': ['card'],
            'allow_promotion_codes': False,
            'automatic_tax': {'enabled': False},
            'adaptive_pricing': {'enabled': False},
        }
        raw = self._call(self._client.v1.checkout.sessions.create, params,
                         options={'idempotency_key': idempotency_key}, creation=True)
        expected = dict(price_id=price_id, success_url=success_url,
                        cancel_url=cancel_url, client_reference_id=client_reference_id,
                        operation_id=operation_id)
        try:
            session = self._session(raw, expected=expected)
            if session.status != 'open' or session.payment_status != 'unpaid':
                raise StripeProviderDataError('provider_session_mismatch')
        except StripeProviderDataError as exc:
            raise ProviderUncertain('stripe_created_session_requires_review') from exc
        return session

    def get_intent(self, intent_id):
        self._account()
        if not isinstance(intent_id, str) or not intent_id.startswith('pi_'):
            raise StripeProviderDataError('provider_intent_identity')
        raw = self._call(self._client.v1.payment_intents.retrieve, intent_id)
        _test_object(raw)
        if _text(raw, 'id') != intent_id:
            raise StripeProviderDataError('provider_intent_identity')
        intent = ProviderIntent(
            intent_id, self.account_id, 'test', _time(raw, 'created'),
            _text(raw, 'status'), _text(raw, 'capture_method'),
            _integer(raw, 'amount', positive=True), _integer(raw, 'amount_received'),
            _text(raw, 'currency').upper())
        self._intents[intent_id] = intent
        return intent

    def get_all_lines(self, session_id):
        self._account()
        result = self._call(self._client.v1.checkout.sessions.line_items.list,
                            session_id, params={'limit': 100})
        if not hasattr(result, 'auto_paging_iter'):
            raise StripeProviderDataError('provider_lines_incomplete')
        lines = []
        try:
            for raw in result.auto_paging_iter():
                price = _value(raw, 'price')
                if price is None:
                    raise StripeProviderDataError('provider_line_incomplete')
                lines.append(ProviderLine(
                    _text(price, 'id'), _id(_value(price, 'product')),
                    _integer(raw, 'quantity', positive=True),
                    _integer(raw, 'amount_total', positive=True),
                    _text(raw, 'currency').upper()))
                if len(lines) > 1:
                    break
        except stripe.StripeError as exc:
            raise ProviderUnavailable('stripe_lines_unavailable') from exc
        return tuple(lines)

    def find_success_events(self, intent_id):
        self._account()
        intent = self._intents.get(intent_id)
        if intent is None:
            raise StripeProviderDataError('provider_intent_not_queried')
        result = self._call(self._client.v1.events.list, params={
            'type': 'payment_intent.succeeded',
            'created': {'gte': int(intent.created.timestamp())},
            'limit': 100,
        })
        if not hasattr(result, 'auto_paging_iter'):
            raise StripeProviderDataError('provider_events_incomplete')
        found = []
        try:
            for index, raw in enumerate(result.auto_paging_iter()):
                if index >= 1000:
                    raise ProviderUnavailable('stripe_event_search_incomplete')
                _test_object(raw)
                if _text(raw, 'type') != 'payment_intent.succeeded':
                    raise StripeProviderDataError('provider_event_type')
                account = _value(raw, 'account')
                if account not in (None, self.account_id):
                    raise StripeProviderDataError('provider_account_mismatch')
                object_id = _id(_value(_value(raw, 'data'), 'object'))
                if not object_id.startswith('pi_'):
                    raise StripeProviderDataError('provider_event_object')
                if object_id == intent_id:
                    found.append(ProviderEvent(_text(raw, 'id'), self.account_id, 'test',
                        'payment_intent.succeeded', object_id, _time(raw, 'created')))
                    if len(found) > 1:
                        break
        except stripe.StripeError as exc:
            raise ProviderUnavailable('stripe_events_unavailable') from exc
        return tuple(found)
