# Part C HTTP Layer — V1

## Scope

This contract describes the local HTTP adapters for `apps.bank` and `apps.shop`.
It does not change the global URL configuration, authentication ownership,
wallet provisioning, financial services, inventory services, or database schema.

## Routes

| Namespace | Method | Relative path | Purpose |
|---|---|---|---|
| `bank` | GET | `wallet/` | Authenticated wallet summary and paginated ledger history |
| `shop` | GET | `` | Authenticated catalog of eligible active offers |
| `shop` | GET | `<sku_code>/` | Offer details and purchase form |
| `shop` | POST | `<sku_code>/purchase/` | Purchase through `purchase_item` |
| `shop` | GET | `purchases/` | Purchase history for the authenticated user |

The URL modules declare namespaces `bank` and `shop`. Core owns the final
prefixes and global mounting. The templates extend `duckies/base.html`; therefore
an integration URLconf must also mount the `duckies` namespace. No global route is
activated by this change.

## Security and domain boundaries

- All Bank and Shop pages require an authenticated session.
- Purchase is POST-only and relies on Django CSRF middleware and `{% csrf_token %}`.
- User identity always comes from `request.user`; no user ID is accepted from forms.
- The purchase form accepts only `quantity` and a generated `operation_key`.
  It does not accept price, balance, wallet ID, or delivery quantity.
- Catalog and detail queries expose only active, available offers whose item
  category, consumable flag, and optional level match the current Shop V1 rules.
- The purchase view delegates price calculation, balance debit, idempotency,
  delivery, and persistence exclusively to `apps.shop.services.purchase_item`.
- Wallet summary and ledger history delegate to the existing Bank services and
  filter movements by the authenticated user.
- Purchase history is filtered by `request.user` and is never global.
- Missing wallets are displayed as not provisioned. HTTP requests do not create
  wallets or Duckies; provisioning remains an authorized Core/Ecomotor workflow.
- Database failures return HTTP 503. Invalid forms return HTTP 400. Domain
  conflicts return HTTP 409. Missing catalog offers return HTTP 404.

## Idempotency

The detail page issues a random operation key for the purchase form. The key is
submitted unchanged on browser retries of that form. The Shop service remains the
source of truth for replay detection and semantic conflict detection. A new page
render creates a new key; this does not replace the service's idempotency contract.

## Test isolation

The HTTP tests use a dedicated test URLconf that mounts `duckies`, `bank`, and
`shop` under test-only prefixes. This follows the repository's existing isolated
URLconf pattern. It does not imply that Core has mounted these routes in the
application's global URL configuration.

Run from the repository root:

```powershell
.\.venv\Scripts\python.exe manage.py test apps.bank.test_views apps.shop.test_views
.\.venv\Scripts\python.exe manage.py test apps.bank apps.shop
.\.venv\Scripts\python.exe manage.py check
.\.venv\Scripts\python.exe manage.py makemigrations --check --dry-run
```

## Known limitations

- Final route prefixes, menu integration, login URL, and return behavior require
  agreement and implementation by Core.
- Wallet provisioning and Ducky provisioning are intentionally not implemented
  by these HTTP adapters.
- The purchase service's atomicity assumes Bank, Shop, and Duckies share the same
  database transaction and do not independently commit or perform external I/O.
- The current model uses `CASCADE` for Wallet-to-User and Purchase-to-User. A
  financial retention/deletion policy remains a domain decision outside this HTTP
  layer.
- No automatic refund or purchase cancellation endpoint is introduced.
