"""Tests for the authentication and authorization plugin system."""

import pytest
from starlette.requests import Request

from openoma_server.auth.backend import NoOpAuthBackend
from openoma_server.auth.context import AuthContext
from openoma_server.auth.policies import PolicyEngine, Policy, create_default_policy_engine
from openoma_server.auth.permissions import make_permission


class TestAuthContext:
    def test_create_context(self):
        ctx = AuthContext(user_id="u1", tenant_id="t1")
        assert ctx.user_id == "u1"
        assert ctx.tenant_id == "t1"
        assert ctx.attributes == {}

    def test_service_account(self):
        ctx = AuthContext(user_id="svc", tenant_id="t1", attributes={"type": "service"})
        assert ctx.is_service_account is True

    def test_not_service_account(self):
        ctx = AuthContext(user_id="u1", tenant_id="t1", attributes={"type": "user"})
        assert ctx.is_service_account is False

    def test_frozen(self):
        ctx = AuthContext(user_id="u1", tenant_id="t1")
        with pytest.raises(AttributeError):
            ctx.user_id = "u2"


class TestNoOpAuthBackend:
    @pytest.mark.asyncio
    async def test_noop_returns_context(self):
        backend = NoOpAuthBackend()
        # Create a minimal mock request
        from unittest.mock import MagicMock
        request = MagicMock(spec=Request)
        ctx = await backend.authenticate(request)
        assert ctx is not None
        assert ctx.user_id == "local-service"
        assert ctx.tenant_id == "local"
        assert "admin" in ctx.attributes["roles"]


class TestPolicyEngine:
    def test_deny_by_default(self):
        engine = PolicyEngine()
        ctx = AuthContext(user_id="u1", tenant_id="t1")
        assert engine.evaluate("read", "work_block", ctx) is False

    def test_admin_policy(self):
        engine = create_default_policy_engine()
        admin_ctx = AuthContext(
            user_id="admin1", tenant_id="t1", attributes={"roles": ["admin"]}
        )
        assert engine.evaluate("delete", "work_block", admin_ctx) is True
        assert engine.evaluate("read", "contract", admin_ctx) is True

    def test_authenticated_read(self):
        engine = create_default_policy_engine()
        user_ctx = AuthContext(user_id="user1", tenant_id="t1", attributes={"roles": ["viewer"]})
        assert engine.evaluate("read", "work_block", user_ctx) is True

    def test_authenticated_create(self):
        engine = create_default_policy_engine()
        user_ctx = AuthContext(user_id="user1", tenant_id="t1", attributes={"roles": ["editor"]})
        assert engine.evaluate("create", "flow", user_ctx) is True

    def test_unauthenticated_denied(self):
        engine = create_default_policy_engine()
        empty_ctx = AuthContext(user_id="", tenant_id="t1")
        assert engine.evaluate("read", "work_block", empty_ctx) is False

    def test_custom_policy(self):
        engine = PolicyEngine()
        engine.add_policy(
            Policy(
                action="read",
                resource="secret",
                condition=lambda ctx, _: "clearance" in ctx.attributes,
            )
        )
        allowed = AuthContext(user_id="u1", tenant_id="t1", attributes={"clearance": "top"})
        denied = AuthContext(user_id="u2", tenant_id="t1", attributes={})
        assert engine.evaluate("read", "secret", allowed) is True
        assert engine.evaluate("read", "secret", denied) is False


class TestPermissionFactory:
    def test_make_permission_creates_class(self):
        perm_cls = make_permission("read", "widget")
        assert perm_cls.action == "read"
        assert perm_cls.resource == "widget"
        assert "CanReadWidget" in perm_cls.__name__
