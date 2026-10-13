# Single-host deployment prerequisites

These templates require an operator-reviewed Linux host, exact image/input inventory and host-specific acceptance. They do not authorize public deployment, extra resources or DNS changes. Supply the official illustrative workbook separately after rights review; it is not part of the image.

The app runs once on a dedicated internal Docker bridge. The host Caddy process initiates connections to the inspected container address. There is no published app port. Port publication on an internal bridge was unreliable in the tested Docker 29 configuration; this procedure does not depend on it. Verify the actual Docker/network behavior on every target host.

## Required configuration

- `DSF_ORIGIN`: the exact public HTTPS origin accepted by the application.
- `DSF_HOST`: the matching public hostname used by Caddy.
- `DSF_UPSTREAM`: the current, inspected container IP on the dedicated internal bridge followed by `:8080`; use brackets for an IPv6 literal. Supply a literal address, not a public hostname or stale copied address.
- `DSF_REFERENCE_DIR`: a read-only directory containing the reviewed `official.xlsm`.
- `DSF_PREPARED_CACHE`: defaults to `1`; startup preparation remains bounded and fail closed.
- `DSF_WORKSHOP_TEST`: defaults to `0`; explicit `1` remains a provisional capacity setting requiring its own acceptance.

Keep `init: true`. The worker's parent-lifetime check must continue rejecting PID 1; the init process makes the application a normal guarded parent and reaps children. Keep the single process, resource bounds, read-only root, nonroot user, dropped capabilities, no-new-privileges, internal network, disabled container logging and `restart: "no"` settings.

`dns: [127.0.0.1]` specifies a resolver inside the container, where this application runs no DNS server. Docker may still present its embedded resolver in `/etc/resolv.conf` on a user-defined bridge. Inspect and test actual resolution behavior; the configuration line alone is not evidence of DNS isolation. Do not attach an external network as a workaround.

## Install host isolation before application startup

1. Stop/quiesce the owned application. Create or inspect its dedicated internal network without starting the app, and identify the actual Linux bridge interface. Verify that the bridge belongs only to this service. Resolve the interface from Docker and host network state; do not blindly infer its name from a copied network ID.
2. Install an idempotent, operator-owned host INPUT policy for **both IPv4 and IPv6**, scoped to packets arriving on that exact bridge. Use a dedicated chain/comment and preserve unrelated rules. The effective order must be:

   | Scope | Conntrack state | Action |
   | --- | --- | --- |
   | App bridge ingress | `ESTABLISHED,RELATED` | Allow replies to host-initiated connections |
   | App bridge ingress | `NEW` | Drop new connections from the container to host services |

   Place this policy ahead of broader INPUT accept rules. Never flush the host firewall. Check the effective backend and rule order for both address families; do not ignore an unavailable IPv6 control. Retain the policy across the tested restart procedure.
3. The host Caddy process can initiate a connection to the container; replies are conntrack-established traffic. The container must not be able to initiate new connections to host services, including the bridge gateway. An internal bridge alone does not establish this host-access restriction. The INPUT rules complement Docker's forwarding restrictions; they do not by themselves prove every egress path is blocked.
4. Start the app only after verifying those rules. Inspect its address on the dedicated internal network and supply that exact address as `DSF_UPSTREAM`. Refuse missing, ambiguous or wrong-network addresses. Explicitly check that `DSF_UPSTREAM` is set, validate the rendered Caddy configuration and reload Caddy deliberately. Preserve the incoming public Host expected by the application.
5. A recreated container can acquire a new IP. Repeat inspection and proxy validation after recreation; never fall back to a public port bind or an external network. Apply the host firewall policy before every application restart. The policy is not a claim that pre-existing established connections have been revoked; controlled startup order is part of the acceptance evidence.

## Required exact-host receipt

Record the source/image/input identities, Docker/firewall versions, inspected network/bridge/address, effective IPv4/IPv6 rule order and tested restart sequence privately. Do not put operational hostnames, IP addresses or firewall dumps in public source.

Verify host Caddy → app traffic succeeds with the correct Host; no direct public app port exists; new container → host TCP/UDP connections fail for the applicable gateway/host IPv4 and IPv6 addresses; external IPv4/IPv6 and DNS access fail; and the exact official input can calculate and produce queue/chart/packet outputs. Test proxy replies and isolation again after the approved restart/recreation sequence. Include the actual process/memory/failure and logging checks required by the hosted pilot contract.

If bridge identity, firewall control, upstream address or any required isolation check cannot be established, keep the application stopped. Do not weaken the worker guard, logging controls or network isolation to make a smoke test pass. DNS/website publication and spending remain separate approvals.
