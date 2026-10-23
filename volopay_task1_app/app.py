from __future__ import annotations
import json, os, zipfile, io, csv
from pathlib import Path
from datetime import datetime
import pandas as pd
import streamlit as st

APP_DIR = Path(__file__).parent
DATA_DIR = APP_DIR / "data"
EXPORT_DIR = APP_DIR / "exports"
STATE_FILE = APP_DIR / "app_state.json"
EXPORT_DIR.mkdir(exist_ok=True)
ROUTES = ["Sales coaching", "Deal next steps", "Customer follow-up", "Internal/vendor note", "Needs human review", "Intake only — no usable text"]

st.set_page_config(page_title="Revenue Intelligence Inbox", page_icon="📬", layout="wide")


def load_state():
    if STATE_FILE.exists():
        try:
            return json.loads(STATE_FILE.read_text(encoding="utf-8"))
        except Exception:
            pass
    return {"records": {}, "imports": [], "created_at": datetime.now().isoformat(timespec="seconds")}

if "state" not in st.session_state:
    st.session_state.state = load_state()


def save_state():
    STATE_FILE.write_text(json.dumps(st.session_state.state, ensure_ascii=False, indent=2), encoding="utf-8")


def identity(r):
    return f"{r.get('source_type','')}::{r.get('source_id','')}"


def record_text(r):
    p = r.get("payload") or {}
    if r.get("source_type") == "call":
        t = p.get("transcript")
        return t.strip() if isinstance(t, str) and t.strip() else ""
    tp = r.get("transcript_payload") or {}
    turns = tp.get("turns") or []
    return "\n".join(f"{x.get('speaker','Unknown')}: {x.get('text','')}" for x in turns if x.get("text"))


def display_name(r):
    p = r.get("payload") or {}
    if r.get("source_type") == "call":
        return f"Call · {p.get('rep_name') or 'Unknown rep'} · {p.get('observed_outcome') or 'Outcome unknown'}"
    return p.get("title") or f"Meeting · {r.get('record_ref','') }"


def person_name(r):
    p = r.get("payload") or {}
    if r.get("source_type") == "call":
        return p.get("rep_name") or "Unknown call rep"
    return p.get("organizer_email") or "Unknown organiser"


def event_day(r):
    p = r.get("payload") or {}
    stamp = p.get("started_at") if r.get("source_type") == "call" else p.get("starts_at")
    if not stamp: return "Unknown date"
    try:
        return pd.to_datetime(stamp, utc=True).tz_convert("Asia/Kolkata").strftime("%Y-%m-%d")
    except Exception: return str(stamp)[:10]


def suggest_route(r):
    text = record_text(r).lower()
    if not text:
        return ["Intake only — no usable text"], "No usable supplied transcript text; keep in intake review and do not infer what happened."
    routes, reasons = [], []
    if any(k in text for k in ["coach", "practice", "objection", "discovery", "ask questions", "talking too much", "next time"]):
        routes.append("Sales coaching"); reasons.append("Conversation contains sales approach, objection handling, or coaching signals.")
    if any(k in text for k in ["next step", "follow up", "follow-up", "send over", "send you", "by friday", "tomorrow", "raise it", "check with the team", "will share"]):
        routes.append("Deal next steps"); reasons.append("Conversation contains an explicit action, commitment, or next step.")
    if any(k in text for k in ["customer", "client", "invoice", "payment", "upload", "support", "issue", "workaround", "not working", "doesn't work", "does not work"]):
        routes.append("Customer follow-up"); reasons.append("Conversation includes a customer-reported issue, request, or follow-up need.")
    if any(k in text for k in ["vendor", "internal", "engineering", "product team", "team investigate", "raise with the team", "bug"]):
        routes.append("Internal/vendor note"); reasons.append("Conversation includes an internal investigation, product issue, or vendor/team dependency.")
    if not routes:
        routes = ["Needs human review"]
        reasons = ["Text is available, but the deterministic starter rules did not find a confident route; manager review is needed."]
    return list(dict.fromkeys(routes)), " ".join(reasons)


def analyse(r):
    text = record_text(r)
    routes, reason = suggest_route(r)
    if not text:
        return {"summary": "No usable supplied transcript. Review metadata only; do not infer conversation content.", "evidence": [], "next_action": "Check source metadata and leave substantive analysis pending until usable text is available.", "suggested_routes": routes, "route_reason": reason, "analysis_revision": r.get("applied_revision", 1), "analysis_status": "intake only"}
    # Compact, transparent extractive analysis: no claim that an LLM was called.
    sentences = [s.strip() for s in text.replace("\n", " ").split(".") if len(s.strip()) > 35]
    evidence = sentences[:3]
    summary = (evidence[0][:360] + ("…" if len(evidence[0]) > 360 else "")) if evidence else "Transcript text is available; inspect the full evidence before deciding."
    action = "Manager to review the cited evidence and confirm an owner and due date; do not assume ownership unless explicitly stated."
    if any(k in text.lower() for k in ["workaround", "upload", "not appearing", "still the old", "cannot upload", "does not work"]):
        action = "Track the reported product/customer issue, preserve the workaround as temporary, and confirm resolution with the customer."
    elif any(k in text.lower() for k in ["send", "follow up", "tomorrow", "friday", "raise it", "share"]):
        action = "Confirm the stated follow-up, owner and due date; keep any unstated owner/date marked unknown."
    return {"summary": summary, "evidence": evidence, "next_action": action, "suggested_routes": routes, "route_reason": reason, "analysis_revision": r.get("applied_revision", 1), "analysis_status": "prepared rule-based extract; review recommended"}


def import_batch(batch, label="uploaded batch"):
    revision = int(batch.get("revision", 1))
    incoming = batch.get("records", [])
    state = st.session_state.state
    added = updated = ignored = 0
    for source in incoming:
        key = identity(source)
        current = state["records"].get(key)
        if current is None:
            item = dict(source)
            item["applied_revision"] = revision
            item["manual_route"] = None
            item["manual_route_note"] = ""
            item["route_status"] = "suggested"
            item["analysis"] = analyse(item)
            state["records"][key] = item
            added += 1
        elif revision > int(current.get("applied_revision", 1)):
            old_text = record_text(current)
            preserved_route = current.get("manual_route")
            item = dict(source)
            item["applied_revision"] = revision
            item["manual_route"] = preserved_route
            item["manual_route_note"] = current.get("manual_route_note", "")
            item["route_status"] = "manual override" if preserved_route else "suggested"
            new_text = record_text(item)
            item["analysis"] = analyse(item)
            if old_text != new_text:
                item["analysis"]["analysis_status"] = "needs review after source update"
            state["records"][key] = item
            updated += 1
        else:
            ignored += 1
    state["imports"].append({"label": label, "batch_id": batch.get("batch_id", "unknown"), "revision": revision, "received_records": len(incoming), "added": added, "updated": updated, "ignored": ignored, "at": datetime.now().isoformat(timespec="seconds")})
    save_state()
    return added, updated, ignored


def current_route(r):
    return [r["manual_route"]] if r.get("manual_route") else r.get("analysis", {}).get("suggested_routes", ["Needs human review"])


def make_exports():
    records = list(st.session_state.state["records"].values())
    root = EXPORT_DIR / "revenue_intelligence_export"
    if root.exists():
        import shutil; shutil.rmtree(root)
    (root / "outputs").mkdir(parents=True)
    manifest = []
    for r in records:
        text = record_text(r)
        route_list = current_route(r)
        base = f"{r.get('record_ref','record')}_{r.get('source_type','source')}_{r.get('source_id','unknown')[:8]}"
        paths = []
        if text:
            for ix, route in enumerate(route_list, 1):
                slug = "_".join("".join(c.lower() if c.isalnum() else "_" for c in route).split())
                rel = f"outputs/{base}_{ix}_{slug}.md"
                (root / rel).write_text(
                    f"# {display_name(r)}\n\n- Record reference: {r.get('record_ref')}\n- Source type: {r.get('source_type')}\n- Source ID: {r.get('source_id')}\n- Applied revision: {r.get('applied_revision')}\n- Route: {route}\n- Route status: {r.get('route_status','suggested')}\n- Analysis status: {r.get('analysis',{}).get('analysis_status','unknown')}\n\n## Summary\n{r.get('analysis',{}).get('summary','')}\n\n## Why this route was suggested\n{r.get('analysis',{}).get('route_reason','')}\n\n## Evidence excerpts\n" + "\n\n".join(f"> {e}" for e in r.get('analysis',{}).get('evidence',[])) + f"\n\n## Next action\n{r.get('analysis',{}).get('next_action','')}\n", encoding="utf-8")
                paths.append(rel)
        manifest.append({"record_ref": r.get("record_ref"), "source_type": r.get("source_type"), "source_id": r.get("source_id"), "applied_source_revision": r.get("applied_revision"), "routes": route_list, "output_paths": paths, "processing_review_state": r.get("analysis",{}).get("analysis_status", "pending"), "manual_override": bool(r.get("manual_route")), "analysis_freshness": "stale_or_review_needed" if "needs review" in r.get("analysis",{}).get("analysis_status", "") else ("current" if r.get("analysis",{}).get("analysis_revision") == r.get("applied_revision") else "stale")})
    (root / "manifest.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")
    pd.DataFrame(manifest).to_csv(root / "manifest.csv", index=False)
    brief = ["# Manager brief — 21 August 2026 (Asia/Kolkata)", "", f"Records in current state: {len(records)}", f"Usable supplied texts: {sum(bool(record_text(r)) for r in records)}", "", "## Review priorities", "- Review conversations with a manual route override or a source update marked as needing review.", "- Do not treat missing transcript text as proof that a conversation did not happen.", "- Confirm owners and due dates where the source text does not explicitly establish them.", "", "## Conversations requiring attention"]
    priority = [r for r in records if record_text(r) and (r.get("manual_route") or any(k in record_text(r).lower() for k in ["not working", "cannot upload", "not appearing", "not interested", "workaround", "follow up", "raise it"]))]
    for r in priority[:12]:
        brief += [f"### {r.get('record_ref')} — {display_name(r)}", f"- Route: {', '.join(current_route(r))}", f"- Evidence: {(r.get('analysis',{}).get('evidence') or ['Inspect full transcript'])[0]}", f"- Next action: {r.get('analysis',{}).get('next_action','Review')} ", ""]
    (root / "manager_brief.md").write_text("\n".join(brief), encoding="utf-8")
    zip_path = EXPORT_DIR / "revenue_intelligence_export.zip"
    if zip_path.exists(): zip_path.unlink()
    with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as z:
        for p in root.rglob("*"):
            if p.is_file(): z.write(p, p.relative_to(root.parent))
    return zip_path, root


# Header
st.title("📬 Revenue Intelligence Inbox")
st.caption("A manager workspace for call and meeting intake, evidence-led routing, updates and exports.")

with st.sidebar:
    st.header("Import & replay")
    st.caption("Use the provided initial and update batches to reproduce the required replay test.")
    if st.button("Import initial batch (revision 1)", use_container_width=True):
        b = json.loads((DATA_DIR / "01_initial.json").read_text(encoding="utf-8")); a,u,i = import_batch(b, "bundled initial batch"); st.success(f"Added {a}, updated {u}, ignored {i}."); st.rerun()
    if st.button("Import update batch (revision 2)", use_container_width=True):
        b = json.loads((DATA_DIR / "02_update.json").read_text(encoding="utf-8")); a,u,i = import_batch(b, "bundled update batch"); st.success(f"Added {a}, updated {u}, ignored {i}."); st.rerun()
    uploaded = st.file_uploader("Or import a JSON delivery", type=["json"])
    if uploaded is not None and st.button("Apply uploaded delivery", use_container_width=True):
        try:
            b = json.loads(uploaded.getvalue().decode("utf-8")); a,u,i = import_batch(b, uploaded.name); st.success(f"Added {a}, updated {u}, ignored {i}."); st.rerun()
        except Exception as e: st.error(f"Could not import JSON: {e}")
    st.divider()
    if st.button("Reset to clean start", use_container_width=True):
        st.session_state.state = {"records": {}, "imports": [], "created_at": datetime.now().isoformat(timespec="seconds")}; save_state(); st.rerun()
    st.caption("State persists in app_state.json. For the required demo: import initial twice, correct M07, import update, import initial again, then refresh/restart.")

records = list(st.session_state.state["records"].values())
if not records:
    st.info("Start by clicking **Import initial batch (revision 1)** in the sidebar. The dashboard and conversation inbox will populate from the supplied records.")
    st.stop()

# filters
f1, f2, f3 = st.columns([1,1,2])
people = sorted(set(person_name(r) for r in records))
with f1: source_filter = st.selectbox("Source type", ["All", "call", "meeting"])
with f2: person_filter = st.selectbox("Person / organiser", ["All"] + people)
with f3: search = st.text_input("Search records or transcript", placeholder="Search title, person, reference, transcript…")
filtered = []
for r in records:
    if source_filter != "All" and r.get("source_type") != source_filter: continue
    if person_filter != "All" and person_name(r) != person_filter: continue
    hay = " ".join([str(r.get("record_ref", "")), display_name(r), person_name(r), record_text(r)]).lower()
    if search.lower().strip() not in hay: continue
    filtered.append(r)

usable = sum(bool(record_text(r)) for r in filtered)
manuals = sum(bool(r.get("manual_route")) for r in filtered)
needs_review = sum("needs review" in r.get("analysis",{}).get("analysis_status", "") or r.get("analysis",{}).get("analysis_status") == "intake only" for r in filtered)
c1,c2,c3,c4 = st.columns(4)
c1.metric("Selected records", len(filtered), help="Unique records after deduplication, filtered by source/person/search.")
c2.metric("Usable supplied text", f"{usable}/{len(filtered)}" if filtered else "0/0", help="Records with non-empty supplied transcript text. Missing text is not proof the conversation did not happen.")
c3.metric("Manual route overrides", manuals)
c4.metric("Needs review / intake", needs_review)

with st.expander("Metric definitions & data limitations"):
    st.write("Counts are based on the selected source records after filtering. Identity is (source_type, source_id). Call reps and meeting organisers are different roles and are not treated as interchangeable. The extract is selected for variety, not representative team performance. No pipeline value or deal outcome is inferred. All event dates are interpreted in Asia/Kolkata for display.")

left, right = st.columns([1.15, 1])
with left:
    st.subheader("Activity by person / organiser")
    if filtered:
        chart_df = pd.DataFrame([{"Person / organiser": person_name(r), "Source type": r.get("source_type"), "Record": 1} for r in filtered])
        pivot = chart_df.groupby(["Person / organiser", "Source type"], as_index=False)["Record"].sum()
        st.bar_chart(pivot.pivot(index="Person / organiser", columns="Source type", values="Record").fillna(0))
    st.subheader("Activity by local date")
    if filtered:
        day_df = pd.DataFrame([{"Local date (IST)": event_day(r), "Source type": r.get("source_type"), "Records": 1} for r in filtered])
        st.bar_chart(day_df.groupby(["Local date (IST)", "Source type"])["Records"].sum().unstack(fill_value=0))
with right:
    st.subheader("Routing & review state")
    route_rows = []
    for r in filtered:
        for route in current_route(r): route_rows.append({"Route": route, "Records": 1})
    if route_rows: st.bar_chart(pd.DataFrame(route_rows).groupby("Route")["Records"].sum())
    st.subheader("Recent import log")
    logs = st.session_state.state.get("imports", [])[-8:]
    if logs: st.dataframe(pd.DataFrame(logs).iloc[::-1], use_container_width=True, hide_index=True)
    else: st.caption("No import activity yet.")

st.divider()
st.subheader("Conversation inbox")
st.caption("Choose a record to inspect evidence, understand its suggested route, and save a manual correction.")
options = {f"{r.get('record_ref')} · {display_name(r)} · {'text' if record_text(r) else 'no text'}": identity(r) for r in filtered}
if not options:
    st.warning("No records match the current filters.")
else:
    selected_label = st.selectbox("Select a conversation / source record", list(options.keys()))
    selected_key = options[selected_label]
    rec = st.session_state.state["records"][selected_key]
    p = rec.get("payload") or {}
    a = rec.get("analysis") or {}
    d1,d2,d3 = st.columns(3)
    d1.write(f"**Reference:** {rec.get('record_ref')}  \n**Type:** {rec.get('source_type')}  \n**Revision:** {rec.get('applied_revision')}")
    d2.write(f"**Person / organiser:** {person_name(rec)}  \n**Local date:** {event_day(rec)}  \n**Text available:** {'Yes' if record_text(rec) else 'No'}")
    d3.write(f"**Current route:** {', '.join(current_route(rec))}  \n**Route status:** {rec.get('route_status','suggested')}  \n**Analysis status:** {a.get('analysis_status','pending')}")
    st.markdown("#### Analysis and suggested action")
    st.write(a.get("summary", "No analysis available."))
    st.info(a.get("next_action", "Review source record."))
    st.caption("Routing reason: " + a.get("route_reason", "No reason available."))
    st.markdown("#### Evidence from supplied source text")
    if record_text(rec):
        if rec.get("source_type") == "meeting":
            turns = (rec.get("transcript_payload") or {}).get("turns", [])
            for idx, turn in enumerate(turns, 1):
                st.markdown(f"**Turn {idx} · {turn.get('speaker','Unknown')} · {turn.get('timecode','time not supplied')}**")
                st.write(turn.get("text", ""))
        else:
            st.text_area("Full call transcript", value=record_text(rec), height=180, disabled=True)
        with st.expander("Source payload details (for audit)"):
            st.json({k:v for k,v in rec.items() if k not in ["analysis"]})
    else:
        st.warning("No usable transcript text supplied for this record. The app keeps the record visible for intake/review but does not invent conversation analysis.")
    st.markdown("#### Manual routing decision")
    default_route = rec.get("manual_route") or (a.get("suggested_routes") or [ROUTES[-1]])[0]
    idx = ROUTES.index(default_route) if default_route in ROUTES else 0
    new_route = st.selectbox("Set one primary manual route", ROUTES, index=idx, key=f"route_{selected_key}")
    note = st.text_input("Reason for manual decision (recommended)", value=rec.get("manual_route_note", ""), key=f"note_{selected_key}")
    b1,b2 = st.columns(2)
    with b1:
        if st.button("Save manual route", type="primary", use_container_width=True):
            rec["manual_route"] = new_route
            rec["manual_route_note"] = note
            rec["route_status"] = "manual override"
            save_state(); st.success("Manual route saved and persisted."); st.rerun()
    with b2:
        if st.button("Reset to suggested route", use_container_width=True):
            rec["manual_route"] = None; rec["manual_route_note"] = ""; rec["route_status"] = "suggested"; save_state(); st.success("Manual override removed."); st.rerun()

st.divider()
st.subheader("Manager brief & exports")
st.write("Export the current post-update state into per-route Markdown outputs plus a JSON/CSV manifest. The manifest records source identity, revision, routes, output paths, review state, override status and analysis freshness.")
if st.button("Generate / refresh exports", type="primary"):
    zp, root = make_exports(); st.session_state["export_zip_path"] = str(zp); st.session_state["export_root"] = str(root); st.success(f"Exports generated for {len(records)} source records.")
if st.session_state.get("export_zip_path") and Path(st.session_state["export_zip_path"]).exists():
    zp = Path(st.session_state["export_zip_path"])
    st.download_button("Download export archive (.zip)", data=zp.read_bytes(), file_name=zp.name, mime="application/zip")
    root = Path(st.session_state["export_root"])
    if (root / "manager_brief.md").exists():
        with st.expander("Preview manager brief"):
            st.markdown((root / "manager_brief.md").read_text(encoding="utf-8"))

st.caption("Prototype note: routing suggestions and summaries use transparent deterministic rules and extractive snippets, not a live AI model. Review all recommendations before acting. Source data is adapted/de-identified for this assignment.")
