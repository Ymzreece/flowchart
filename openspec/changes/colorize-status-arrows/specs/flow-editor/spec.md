# Flow Editor — Status-Colored Arrows

## ADDED Requirements

### Requirement: Stage 2 edge metadata accepts lifecycle status
Stage 2 modules SHALL allow edges to include an optional lifecycle status flag without breaking existing tooling.

#### Scenario: Stage 2 module declares a recognised edge status
- Given a Stage 2 module JSON whose edge entry contains `metadata: { "status": "<value>" }`
- And `<value>` is one of `default`, `active`, `success`, `warning`, `error`, or `disabled`
- When the module is validated or loaded by existing tooling
- Then the schema/type definitions treat `metadata.status` as an optional string constrained to the supported set
- And Stage 1 → Stage 2 converters in `flowcode_renderer` persist the status without modification.

#### Scenario: Stage 2 module omits status metadata
- Given a Stage 2 module JSON whose edge omits `metadata.status`
- When the Python converter or React editor loads the graph
- Then the edge remains valid and retains the current neutral styling behaviour.

### Requirement: Flow editor visualises edge status with color-coded arrows
Edges with lifecycle statuses SHALL render with consistent color treatments in the React Flow canvas.

#### Scenario: Rendering an edge with a recognised status
- Given the React Flow editor receives an edge whose `metadata.status` is one of the supported values
- When the canvas renders the edge
- Then the stroke, arrowhead, and badge background use the status palette (e.g., `success` → green, `error` → red)
- And the styling meets WCAG AA contrast against the canvas background
- And selection/highlight states layer on top without obscuring the base status color.

#### Scenario: Rendering an edge with an unrecognised status
- Given the React Flow editor receives an edge whose `metadata.status` is not in the supported set
- When the canvas renders the edge
- Then the edge falls back to the neutral stroke used today
- And a console warning (in development mode) indicates the unsupported status value.

### Requirement: Flow editor exposes a status legend
Viewers SHALL be able to reference an always-on legend that maps edge colors to their status labels.

#### Scenario: Viewing a graph that contains at least one recognised status
- Given the Flow editor loads a graph where any edge declares a supported status value
- When the UI renders shell chrome (toolbar/sidebar)
- Then a non-dismissable legend summarises each status label and color token
- And the legend uses text labels (not color alone) so that assistive technologies can convey the mapping.
