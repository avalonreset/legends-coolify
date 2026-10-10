# Knowledge maintenance

Maintain one canonical explanation per topic and link to it from recipes. Add knowledge when it changes a decision or prevents a repeated failure.

## Update loop

1. Identify a source change, observed failure, or unanswered operational question.
2. Read the relevant official documentation and capture the retrieval date and applicable version, if known.
3. Distinguish documented behavior, privately verified behavior, and module recommendation. Never imply a live test from a documentation read.
4. Update the smallest affected note and its [source ledger](sources.md) coverage.
5. Check links, public/private boundaries, command accuracy, and whether the agent recipe points to the right note.
6. Add a concise entry to [log](log.md), including remaining uncertainty.

Recheck version-sensitive guidance before releases and consequential operations, especially permissions, response schemas, backup support, and rollback behavior. Record unknown versions honestly rather than inventing a compatibility matrix.

The [source update template](templates/source-update.md) is for reusable research changes. The [private receipt template](templates/private-operation-receipt.md) is for actual operations. Neither substitutes for acceptance evidence.

This vault follows source-ledger and linked-knowledge practices. It does not claim a Brainstein audit score or use an automated scaffold as evidence of quality. Public router discovery must be proven independently; adding Markdown here does not register a module in a catalog.
