-- First, let's drop the existing policy that might be misconfigured
DROP POLICY IF EXISTS "Allow public insert to raw_daily_prices" ON public.raw_daily_prices;
DROP POLICY IF EXISTS "Allow public select on raw_daily_prices" ON public.raw_daily_prices;

-- Recreate the INSERT policy explicitly for both 'anon' and 'authenticated'
CREATE POLICY "Allow public insert to raw_daily_prices"
ON public.raw_daily_prices
FOR INSERT
TO public
WITH CHECK (true);

-- The Python Supabase client performs an "INSERT ... RETURNING *" by default.
-- Because of this, it needs SELECT access to the row it just inserted.
-- We must add a SELECT policy as well, otherwise the insert will fail!
CREATE POLICY "Allow public select on raw_daily_prices"
ON public.raw_daily_prices
FOR SELECT
TO public
USING (true);

-- Ensure RLS is active
ALTER TABLE public.raw_daily_prices ENABLE ROW LEVEL SECURITY;
