# Environment, TLS and CORS

Treat configuration correctness as multiple independent checks.

## Environment

`env --uuid` lists variable names; it does not verify values or expose them. Distinguish build-time, runtime, preview, and shared configuration. A saved variable can differ from what a running container uses until the appropriate recreation or build occurs. [Environment variables](https://coolify.io/docs/applications/configuration/environment-variables)

Recommendation: compare required names against application documentation, then validate behavior using an authorized private workflow. Do not infer that a present name has a valid value, or publish connection strings to prove configuration.

## Routing and TLS

Confirm the hostname resolves to the intended ingress and that the configured route points to the actual internal listening port. Coolify's HTTPS routing can request certificates through its proxy, but issuance depends on DNS and network reachability. A working dashboard certificate says nothing about a different application's domain. [Domains](https://coolify.io/docs/core/networking/domains)

## Browser access

CORS is browser enforcement of cross-origin access. A successful command-line request does not establish browser success. Check the actual frontend origin, requested method and headers, preflight result when applicable, and credentials policy. Credentialed access cannot use a wildcard allowed origin. [MDN CORS](https://developer.mozilla.org/en-US/docs/Web/HTTP/Guides/CORS)

Module recommendation: change application or proxy CORS configuration only after identifying which layer owns the response. Do not disable browser security or widen origins indiscriminately to hide a routing failure.

See [health layers](inventory-and-health.md) and [troubleshooting](troubleshooting.md).
