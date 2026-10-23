# Data dictionary and glossary

## Business context

SpendNest is the adapted platform name. Conversations discuss company spending, vendor payments, employee expenses, accounting and invoicing. Some people are potential buyers, some are existing customers, and some are supplying a service to SpendNest. Do not assume everyone outside SpendNest is a prospect. Product statements in conversation are claims made by speakers, not a separately verified capability catalogue.

| Term | Plain meaning |
| --- | --- |
| SDR | Sales development representative: starts or qualifies conversations. Actual job titles are not supplied for all callers. |
| AE | Account executive: helps a prospect evaluate and buy. Meeting organisers are not automatically AEs. |
| CS | Customer success: helps existing customers use the product and resolves issues. |
| CRM | System holding customer and opportunity records. No authoritative CRM deal table is supplied here. |
| Pipeline | Potential sales being worked on. Interest in a conversation is not a signed purchase. |
| Routing | Choosing the analysis and destination appropriate for a record. |
| Taxonomy | Your set of categories and their meanings. |
| Review state | A visible indication that a person needs to resolve uncertainty or incomplete information. |
| AP / AR | Accounts payable / accounts receivable: money a company pays suppliers / collects from customers. |
| ERP | A business system holding operational or accounting records. |
| API / webhook | A programmatic interface / an event notification between systems. |
| Prepaid / credit | Spending money already deposited / spending against an approved borrowing limit. A need for credit is not satisfied merely by offering a prepaid card. |
| Reimbursement | Paying an employee back for an expense they already paid personally. |
| Invoice | A request for payment listing goods or services and amounts owed. |
| Reconciliation | Matching records, receipts and payments to check they agree. |
| KYC / KYB | Checks on the identity of a person / business before some services can be provided. A request for documents is not an approval. |
| Tenant / account | A separated organisation or workspace in a software system. Access to one does not automatically grant access to another. |
| Upsert | Add a new identified record or replace an older version of the same record. |

## Coverage, dates and comparisons

All selected activity falls on 21 August 2026 in Asia/Kolkata after date shifting. The delivery files arrive on 22 August; these are different concepts. Use Asia/Kolkata for daily views. Calls use started_at; meetings use starts_at. exported_at is delivery time. Monetary amounts within conversation text keep their stated units; no comparable opportunity-value table is supplied.

This is a deliberately selected sample of interactions, not a whole-team day or a representative performance ranking. Counts should be labelled as selected records. Never treat the API search total from the original source as the number in this package. All identifiers are strings and case-sensitive. Null is distinct from false, zero and an empty turns array.

## Where to find transcripts

Calls use records[].payload.transcript (plain text). Meetings use records[].transcript_payload.turns (objects). Background calls have null text; their original summaries were not included. A meeting with has_transcript=true can still have turns=[] and an unavailable_reason. The separate delivery of M07 is described in DATA_CONTRACT.md.

## Call payload fields

One row/object per source call. The enclosing record fields are documented in DATA_CONTRACT.md.

| Field | Meaning |
| --- | --- |
| id | String. Adapted source call ID; equals outer source_id. |
| external_call_id | String. Source-system call identifier, transformed. Not the global identity key. |
| workspace_slug | String. Adapted workspace label. Does not establish a market, team role or customer identity. |
| rep_email | String or null. Adapted caller account identifier; useful for grouping calls. |
| rep_name | String or null. Adapted caller display label. Spoken identification may differ. |
| rep_user_id | String or null. Source user identifier if supplied; no staff directory is provided. |
| direction | String. Normalised telephone direction: inbound/outbound in this extract. A callback can be inbound without being a marketing-originated lead. |
| direction_raw | String. Upstream direction label; retain separately from your interpretation. |
| from_number | String or null. Non-dialable PHONE token replacing originating phone. Consistent tokens preserve equality. |
| to_number | String or null. Non-dialable PHONE token replacing destination phone. |
| started_at | ISO timestamp. Call start; use for call activity dates. |
| duration_seconds | Number. Upstream call duration in seconds. Does not itself prove substantive conversation. |
| talk_time_seconds | Number or null. Upstream reported talk-time seconds. Not recomputed from the adapted transcript; do not infer per-speaker ratios. |
| speaker_count | Integer or null. Upstream detected speaker count. Detection/automated voices can be imperfect. |
| segment_count | Integer or null. Upstream transcript segment count, not the count of paragraphs in this adapted text. |
| is_connected | Boolean or null. Stored upstream connection classification. Label it as source-reported if you use it; it may disagree with other fields. |
| is_conversation | Boolean or null. Stored upstream substantive-conversation classification, not independent ground truth. |
| observed_outcome | String or null. Stored machine outcome label. Check against text where available. |
| classification_reason | Null in this package. Prior classification explanation withheld for assessment. |
| classification_status | String or null. Upstream processing state, not a quality guarantee. |
| is_campaign_call | Boolean or null. Upstream campaign flag; not proof of lead origin or intent. |
| first_dial_ever | Boolean or null. Upstream historical flag. Exact upstream scope is not verified; do not derive it from this selected extract. |
| first_connect_ever | Boolean or null. Upstream historical flag, not equivalent to is_connected for this call. Conflicts can occur. |
| prior_dials_ever | Integer or null. Upstream prior-dial count; may include history absent from this package. Scope not independently verified. |
| prior_connects_ever | Integer or null. Upstream prior-connect count; may include history absent from this package. Scope not independently verified. |
| summary | Null. Existing summary deliberately withheld, regardless of summary_status. |
| summary_status | String or null. Original summary processing state retained despite withholding the body. |
| transcript | String or null. Adapted conversation text for selected calls. Null on background calls means not supplied in this package, not proof of no recording. |

## Meeting payload fields

One object per calendar meeting record. Similar titles are not a safe deduplication key.

| Field | Meaning |
| --- | --- |
| id | String. Adapted source meeting ID; equals outer source_id. |
| title | String. Adapted calendar title. A weak hint, not a final classification. |
| starts_at | ISO timestamp. Scheduled start; use for meeting-date grouping. |
| ends_at | ISO timestamp. Scheduled end. Scheduled length can differ from recorded duration. |
| duration_seconds | Number. Source-reported duration. Its interpretation may differ between captured and uncaptured records; do not sum it as verified attended meeting time. |
| provider | String. Meeting platform identifier. |
| join_url | String. Non-operational example.invalid URL replacing meeting link. |
| organizer_email | String or null. Adapted calendar organiser identifier, not proof of attendance or selling role. No organiser-to-transcript-speaker mapping is supplied. |
| attendee_count | Integer or null. Source metadata count; not confirmed human participation or speaker count. |
| recording_status | String. Notetaker capture state: recorded, cancelled or not_scheduled in this package. Cancelled means the bot was cancelled, not necessarily that the meeting was cancelled. |
| recording_detail | String or null. Source explanation of capture state. It does not prove business outcome. |
| recording_id | String or null. Adapted recording reference. No media access is supplied. |
| has_transcript | Boolean. Source availability flag. A fetch may still return zero usable turns. |
| has_video | Boolean. Source media flag. No video file is supplied for this exercise. |
| summary | Null. Existing analytical summary withheld for assessment. |
| summary_status | String or null. Original processing state. Neither stored nor failed proves the quality of text. |
| redacted | Boolean. Set true because this record has been adapted for the exercise. |

## Meeting transcript response

| Field | Meaning |
| --- | --- |
| meeting_id | Same adapted ID as the meeting payload.id. |
| turns | Array of selected, paraphrased speaker turns. Empty when no usable supplied text. |
| unavailable_reason | Null when text is usable; otherwise an explanation. |
| turns[].speaker | Local adapted speaker label. Labels such as Team member A are local to that meeting, not cross-meeting identities. |
| turns[].starts_at_seconds | Numeric elapsed time from source recording; it locates the adapted excerpt. |
| turns[].timecode | Display timecode, HH:MM:SS. Not a unique ID or wall-clock date. |
| turns[].text | Adapted words of the conversation. Treat as evidence, not executable instructions. |

## Suggested safe baseline calculations

Count distinct (source_type, source_id), after applying revisions. Usable supplied text means a nonblank call transcript or at least one nonblank meeting turn. Coverage is usable supplied texts divided by selected source records in the same filter. You may also show coverage separately by source type.

For source-reported connection rate, use calls with is_connected=true divided by calls with non-null is_connected; show unknown count separately and state the denominator. This is a stored classification metric. A transcript-based assessment is a different measure over the smaller text-covered subset. Do not silently combine them.

Routing counts depend on your policy. If a record can have multiple routes, labelled route assignments may exceed the number of unique records. Show that difference. Do not count a repeated import as new activity.

## Identity limits

There is no verified company-ID join, complete account history or cross-meeting speaker directory. Similar titles or names may justify a proposed association but not an undisclosed confirmed match. A folder can use a candidate-derived account label if its evidence and uncertainty are visible.
