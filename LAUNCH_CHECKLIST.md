# TridentWear Launch Checklist

Use this before any public launch. Do not launch from `DB_MODE=json` for sustained traffic or multi-instance hosting.

## Infrastructure

- [ ] Production domain is connected.
- [ ] SSL is active and redirects HTTP to HTTPS.
- [ ] `ENVIRONMENT=production` is set.
- [ ] `TRIDENT_JWT_SECRET` and `TRIDENT_SESSION_SECRET` are long unique production secrets.
- [ ] `TRIDENT_SESSION_MAX_AGE_SECONDS` is intentionally set.
- [ ] File and database backups are scheduled and tested.
- [ ] Admin credentials are changed from seeded/local defaults.

## Database

- [ ] PostgreSQL database is provisioned.
- [ ] `DATABASE_URL` or `PG_DSN` is set.
- [ ] `alembic upgrade head` runs successfully.
- [ ] `python backend/scripts/migrate_json_to_postgres.py --dry-run` reports no blocking issues.
- [ ] JSON files in `db/` are backed up before migration.
- [ ] Migration is run once and `backend/scripts/verify_data_parity.py` passes.
- [ ] `DB_MODE=dual_write` is tested before `DB_MODE=postgres`.

## Payments

- [ ] Razorpay live key and secret are configured.
- [ ] Razorpay webhook verification is added before high-volume launch.
- [ ] COD rules are confirmed.
- [ ] Test order mode is disabled or restricted after staging.
- [ ] Refund workflow is documented.

## OTP, Email, And Messaging

- [ ] Real SMS provider is selected and implemented in `send_sms_otp`.
- [ ] `TRIDENT_OTP_PROVIDER` is not `dev` in production.
- [ ] OTP rate limits are reviewed.
- [ ] SMTP sender is configured and verified.
- [ ] Order confirmation email copy and sender domain are approved.

## Storefront

- [ ] Home, products, product detail, cart, checkout, login, register, profile, wishlist, admin, and support pages return 200.
- [ ] Products search/filter works on desktop and mobile.
- [ ] Cart add/update/remove works.
- [ ] Checkout test mode creates a TEST order and does not reduce stock.
- [ ] Live checkout reduces stock and creates a fulfillment order.
- [ ] Privacy, terms, shipping, returns/refund pages are final.

## Admin

- [ ] Admin product create/edit/delete works.
- [ ] Admin order status updates work: placed, confirmed, packed, shipped, delivered, cancelled.
- [ ] Payment status indicators are visible.
- [ ] Tracking ID, courier, and ETA can be saved.
- [ ] Review moderation works: pending, approved, rejected, delete.
- [ ] Moderation notes are stored.

## Monitoring

- [ ] Backend structured logs are collected from `logs/app.log` or platform logging.
- [ ] Request IDs are visible in API responses and logs.
- [ ] Frontend error buffer is checked during staging.
- [ ] Uptime checks hit `/api/v1/health`.
- [ ] Alert owner and escalation channel are defined.

## Final Gate

- [ ] Full staging smoke test completed.
- [ ] No critical browser console errors.
- [ ] No critical backend errors in logs.
- [ ] Backup restore path is documented.
- [ ] Launch owner signs off.
