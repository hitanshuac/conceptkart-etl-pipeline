-- Fix for the "Security Definer View" lint warning in Supabase
-- This alters the existing dashboard_view to run with security_invoker = true.
-- It ensures that the view respects the Row-Level Security (RLS) policies 
-- of the user querying it, rather than bypassing them.

ALTER VIEW public.dashboard_view SET (security_invoker = true);
