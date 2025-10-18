# OpenSpec Workflow Guide

## When to use OpenSpec
- Trigger this workflow for any request involving planning, architecture, new features, or breaking changes.
- If a task feels ambiguous, review this guide before touching code or docs.
- Informal tweaks that do not alter behaviour (typos, comments) may proceed without a spec, but default to “spec first” if unsure.

## Standard change flow
1. **Gather context**  
   - Review `openspec/project.md`, existing specs (`openspec/specs/`), and prior changes with `openspec list`.  
   - Ask clarifying questions if goals or constraints are unclear.
2. **Create a change shell**  
   - Choose a verb-led `change-id` (e.g., `colorize-status-arrows`).  
   - Scaffold:  
     ```
     openspec/changes/<change-id>/
       proposal.md
       tasks.md
       design.md   (optional, recommended for multi-system work)
       specs/<capability>/spec.md
     ```
3. **Draft proposal.md**  
   - Capture the problem, proposed solution, scope, risks, dependencies, and open questions.  
   - Keep narrative concise and tie back to project goals.
4. **Draft tasks.md**  
   - Break the change into ordered, verifiable work items.  
   - Include validation (tests, tooling) and note parallelisable steps or prerequisites.
5. **Draft design.md (when needed)**  
   - Provide architecture notes, data flows, diagrams, or trade-offs for complex changes.  
   - Skip only for straightforward updates that require no extra reasoning.
6. **Write capability specs**  
   - Each capability goes in its own folder under `specs/`.  
   - Use headers `## ADDED|MODIFIED|REMOVED Requirements`.  
   - Every requirement must state what SHALL/MUST happen and include at least one `#### Scenario:` block describing observable behaviour.  
   - Link related requirements or specs when dependencies exist.
7. **Validate**  
   - Run `openspec validate <change-id> --strict`.  
   - Resolve all errors/warnings before sharing. Validation enforces formatting, SHALL/MUST language, and scenario structure.
8. **Review & iterate**  
   - Share the validated change for review. Incorporate feedback by updating the same files and re-running validation.
9. **Implementation phase**  
   - Reference approved requirements while coding.  
   - Keep implementation commits scoped to the tasks in `tasks.md`.  
   - Add tests/docs listed in the spec; avoid scope creep—open a new change for additional work.
10. **Post-implementation**  
    - Optionally use OpenSpec “apply”/“archive” flows to mark changes as delivered, updating baseline specs if the project uses that workflow regularly.

## Working with AI assistants
- Provide the assistant with the high-level goal; they will consult this file and draft the spec artifacts.  
- Review proposals before coding begins. Confirm assumptions, especially around non-obvious requirements or compatibility.  
- During implementation, reference the approved change ID to keep context aligned. If new scope emerges, pause and author a fresh change.

## Helpful commands
- `openspec list` / `openspec list --specs` — enumerate active changes and base specs.  
- `openspec show <item>` — inspect proposals or specs in detail.  
- `openspec validate <change-id> --strict` — ensure the change meets formatting and structure requirements.  
- `openspec view` — interactive dashboard (when available) for browsing specs/changes.

## Writing tips
- Prefer plain ASCII; keep line lengths reasonable.  
- Use consistent terminology (e.g., Stage 1, Stage 2, FlowGraph) matching `openspec/project.md`.  
- Record assumptions explicitly so future readers understand the rationale.  
- Keep scenarios outcome-focused: describe observable triggers and expectations rather than implementation steps.
