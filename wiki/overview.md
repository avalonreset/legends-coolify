# Overview

`legends-coolify` combines reusable knowledge, small read-only tools, and an agent recipe loaded by the single `cto-legends` router. The vault explains how to interpret observations and what remains unproven after a command succeeds.

The first version inspects resources and prepares decisions. It does not deploy, restart, stop, restore, modify DNS, or change configuration. A plan is an advisory artifact, not an executable migration or authorization to mutate production.

## Evidence model

Separate source claims from live observations and recommendations. Official documentation describes supported behavior; it does not prove a particular instance is configured that way. Tool output is a bounded observation of one instance and time. A release or recovery claim needs evidence from the actual target and a meaningful user flow.

Names, URLs, UUIDs, and status metadata may still be private even when credentials are absent. Public examples use placeholders. [Boundary rules](public-private-boundaries.md) apply to every note.

## Navigation

Use the [index](index.md) to choose the narrowest note. Read the [source ledger](../references/sources.md) when a decision depends on version-sensitive behavior. [Maintenance](knowledge-maintenance.md) describes how evidence becomes reusable knowledge.
