# Revenue Intelligence Inbox

A Streamlit-based Revenue Intelligence Inbox for reviewing supplied sales calls and meeting records, inspecting conversation evidence, routing conversations, replaying source updates, preserving manual routing decisions, and generating traceable exports.

## 1. Project Overview

Sales teams work with information from multiple calls and meetings. Important follow-ups, unresolved customer issues, and next steps can be difficult to track when information is spread across different records.

The Revenue Intelligence Inbox provides a single workspace to:

- Review call and meeting records.
- Search and filter conversations.
- Inspect supplied transcript evidence.
- Suggest conversation routes using transparent rules.
- Flag records that require human review.
- Import initial and updated source deliveries.
- Avoid duplicate records during repeated imports.
- Preserve manager-selected route overrides.
- Track source revisions and analysis freshness.
- Export a manager brief, per-route Markdown files, and JSON/CSV manifests.

## 2. Technology Stack

- **Python** — application logic and data processing.
- **Streamlit** — interactive web interface.
- **JSON** — source data and application state.
- **CSV** — structured export manifest.
- **Markdown** — manager brief and route-specific reports.

The prototype uses deterministic routing rules and extractive evidence snippets. It does not use a live AI model or require a paid AI API.

## 3. Run Locally on Windows

### Prerequisites

- Python 3.11 or a compatible newer version.
- Visual Studio Code.
- The project files and supplied data files.

### Installation

1. Open the project folder in VS Code.
2. Select **Terminal → New Terminal**.
3. Create a virtual environment:

   ```powershell
   py -m venv .venv
   ```

4. Activate the virtual environment:

   ```powershell
   .\.venv\Scripts\Activate.ps1
   ```

   If PowerShell blocks activation, run the following command in the same terminal and try again:

   ```powershell
   Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
   .\.venv\Scripts\Activate.ps1
   ```

5. Install the dependencies:

   ```powershell
   python -m pip install -r requirements.txt
   ```

6. Start the application:

   ```powershell
   python -m streamlit run app.py
   ```

7. Open the local URL shown in the terminal. It is usually:

   `http://localhost:8501`

The application is currently run locally. A public deployment link must be added after deployment has been completed and tested.

## 4. Data Import and Replay Test

The application supports an initial delivery and a later update delivery. The intended replay sequence is:

1. Start from a clean application state.
2. Import `01_initial.json`.
3. Import `01_initial.json` again to test duplicate handling.
4. Open record `M07` and save a manual primary-route correction.
5. Import `02_update.json`.
6. Import `01_initial.json` again to test how an older delivery is handled after an update.
7. Refresh the browser and check that the manual route remains.
8. Generate the exports from the final state.

### Observed test results

The following results were observed during the application replay test:

- **44 unique source records** were present in the final state.
- **18 records** had usable supplied text after the update.
- The manual route override count remained at **1**.
- Record `M07` remained routed to **Customer follow-up** after the update and browser refresh.
- The initial delivery was imported again without increasing the final record count.

The browser refresh confirmed that the saved route was retained. A separate server-restart test should be performed if persistence across a complete application restart needs to be demonstrated.

## 5. M07 Routing Decision

Record `M07` concerns Willowfield Trust and SpendNest.

The supplied conversation describes multiple reported product issues, including:

- Description changes not appearing after saving.
- Direct invoice attachment failing in the Recreate payment workflow, with an alternative workflow available.
- Reimbursements remaining in Processing.
- The Mark as paid action retaining the previous payment amount on the next item.

The record was manually routed to **Customer follow-up** because the reported issues require investigation and a confirmed update to the customer.

The decision preserves the distinction between a reported issue and a verified resolution. The alternative attachment workflow is treated as a workaround, not proof that the underlying issue has been resolved.

The manual route is kept separately from source data so that an imported source update does not automatically erase the manager's routing decision.

## 6. Dashboard Metrics and Definitions

- **Selected records:** Unique logical source records remaining after the current filters are applied. Record identity is based on `(source_type, source_id)`.
- **Usable supplied texts:** Records containing non-empty supplied call transcript text or meeting turns.
- **Manual route overrides:** Records with an explicit manager-selected primary route.
- **Needs review / intake:** Records requiring intake handling or review after a source update.
- **Activity by person / organiser:** Call representatives and meeting organisers are tracked separately. An organiser is not automatically assumed to be the salesperson or an attendee.
- **Analysis freshness:** Indicates whether the existing analysis needs review following a source change.

Dates are displayed in the Asia/Kolkata time zone.

Missing transcript text is not treated as proof that a conversation did not occur. The supplied extract is selected for variety and should not be treated as a representative performance sample. The application does not invent pipeline values, deal outcomes, owners, or due dates.

## 7. Routing and Analysis

The application uses deterministic keyword rules to suggest conversation routes and provide transparent routing reasons. Evidence snippets are extracted from the supplied conversation text.

The routing suggestions are intended to support human decision-making, not replace it. Users should verify recommendations against the original conversation evidence before acting.

When source content changes, the associated analysis can be marked as needing review rather than being presented as unquestionably current.

## 8. Exporting Results

Use **Generate / refresh exports** in the application to export the current state.

The generated ZIP archive contains:

- `manager_brief.md` — a summary of records requiring attention.
- `manifest.json` — a structured record-level export manifest.
- `manifest.csv` — a tabular version of the manifest.
- Per-route Markdown outputs for records with usable text.

The manifest records source identity, applied revision, routes, output paths, review state, manual override status, and analysis freshness.

The archive can be extracted for inspection and included with the assignment deliverables. Confirm that the exported files correspond to the final post-update state before submitting them.

## 9. Known Limitations

- Routing relies on deterministic rules rather than a live AI model.
- Extractive snippets may not capture every important detail in a conversation.
- Route suggestions and summaries require human verification.
- Some records may lack enough supplied text to support a reliable routing decision.
- Analysis may require manual review after source updates.
- Local state persistence does not by itself guarantee persistence on a hosting platform with an ephemeral filesystem.
- Public deployment and hosted persistence must be tested separately from local application behavior.

## 10. Future Improvements

- Improve route-specific analysis using all available conversations.
- Add clearer evidence references to help reviewers verify important decisions.
- Expand automated tests for duplicate imports, revision ordering, and manual override persistence.
- Add stronger validation for malformed or incomplete source deliveries.
- Test persistent storage on the final hosting platform.
- Improve usability and accessibility of the inbox and export workflow.

## 11. Approximate Time Spent

**Development and testing time:** [Enter your actual approximate time spent before submission.]

## 12. Submission Status

- [x] Local application runs.
- [x] Initial and update deliveries imported.
- [x] Duplicate-import behavior checked.
- [x] Manual route override for M07 checked after update and browser refresh.
- [x] Export archive generated and downloaded.
- [ ] README reviewed and saved.
- [ ] Five-slide presentation completed.
- [ ] Three-minute narrated Task 1 screen recording completed.
- [ ] Public deployment completed and link verified.
- [ ] Final deliverables checked before submission.

**Important:** Update the checklist honestly as each item is completed. Do not describe the application as publicly deployed until a reviewer can open the deployed link.

