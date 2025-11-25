-- Migration: Add V2 audit event types
-- Date: 2025-11-25
-- Description: Updates audit_events CHECK constraint to include V2 event types:
--              account_lookup, template_view, mapping_cached

BEGIN;

-- Drop existing constraint
ALTER TABLE audit_events DROP CONSTRAINT IF EXISTS audit_events_event_type_check;

-- Add updated constraint with V2 event types
ALTER TABLE audit_events ADD CONSTRAINT audit_events_event_type_check
    CHECK (event_type IN (
        'search',
        'view',
        'extract',
        'edit',
        'approve',
        'reject',
        'chat',
        'login',
        'logout',
        'user_created',
        'user_updated',
        'user_deleted',
        'account_lookup',
        'template_view',
        'mapping_cached'
    ));

COMMIT;
