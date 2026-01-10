from supabase import create_client, Client
from .config import settings


def supabase_service() -> Client:
    # Service role bypasses RLS; we still enforce ownership checks in API logic.
    return create_client(str(settings.supabase_url), settings.supabase_service_role_key)


def supabase_anon() -> Client:
    return create_client(str(settings.supabase_url), settings.supabase_anon_key)
