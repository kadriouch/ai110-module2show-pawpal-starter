import streamlit as st
from pawpal_system import Owner, Pet, Task, Scheduler

st.set_page_config(page_title="PawPal+", page_icon="🐾", layout="centered")

# --- Session state initialisation ---
if "owner" not in st.session_state:
    st.session_state.owner = None
if "current_pet" not in st.session_state:
    st.session_state.current_pet = None

# ── Title ─────────────────────────────────────────────────────────────────────
st.title("🐾 PawPal+")
st.caption("Your daily pet care planner")
st.divider()

# ── Section 1: Owner setup ────────────────────────────────────────────────────
st.subheader("1. Owner setup")

with st.form("owner_form"):
    col1, col2 = st.columns(2)
    with col1:
        owner_name = st.text_input("Your name", value="Jordan")
    with col2:
        available_minutes = st.number_input(
            "Time available today (minutes)", min_value=0, max_value=480, value=60, step=5
        )
    submitted = st.form_submit_button("Save owner")

if submitted:
    if st.session_state.owner is None:
        st.session_state.owner = Owner(name=owner_name, available_minutes=int(available_minutes))
    else:
        st.session_state.owner.name = owner_name
        st.session_state.owner.set_available_time(int(available_minutes))
    st.success(f"Owner '{owner_name}' saved — {available_minutes} min available today.")

if st.session_state.owner:
    st.info(
        f"Current owner: **{st.session_state.owner.name}** — "
        f"{st.session_state.owner.available_minutes} min available"
    )

st.divider()

# ── Section 2: Add a pet ──────────────────────────────────────────────────────
st.subheader("2. Add a pet")

if st.session_state.owner is None:
    st.warning("Please save your owner info above before adding pets.")
else:
    with st.form("pet_form"):
        col1, col2 = st.columns(2)
        with col1:
            pet_name = st.text_input("Pet name", value="Mochi")
        with col2:
            species = st.selectbox("Species", ["dog", "cat", "rabbit", "bird", "other"])
        add_pet = st.form_submit_button("Add pet")

    if add_pet:
        existing_names = [p.name for p in st.session_state.owner.pets]
        if pet_name in existing_names:
            st.error(f"A pet named '{pet_name}' already exists.")
        else:
            new_pet = Pet(name=pet_name, species=species)
            st.session_state.owner.add_pet(new_pet)
            st.session_state.current_pet = new_pet
            st.success(f"Added {species} '{pet_name}'!")

    if st.session_state.owner.pets:
        pet_names = [p.name for p in st.session_state.owner.pets]
        selected = st.selectbox("Select a pet to add tasks to", pet_names)
        st.session_state.current_pet = next(
            p for p in st.session_state.owner.pets if p.name == selected
        )
    else:
        st.info("No pets yet. Add one above.")

st.divider()

# ── Section 3: Add tasks ──────────────────────────────────────────────────────
st.subheader("3. Add care tasks")

if st.session_state.owner is None or not st.session_state.owner.pets:
    st.warning("Add a pet first before adding tasks.")
elif st.session_state.current_pet is None:
    st.warning("Select a pet above to add tasks to.")
else:
    pet = st.session_state.current_pet
    st.markdown(f"Adding tasks for **{pet.name}** ({pet.species})")

    with st.form("task_form"):
        col1, col2, col3 = st.columns(3)
        with col1:
            task_name = st.text_input("Task name", value="Morning walk")
        with col2:
            duration = st.number_input("Duration (min)", min_value=1, max_value=240, value=20)
        with col3:
            priority = st.selectbox("Priority", ["high", "medium", "low"])
        col4, col5 = st.columns(2)
        with col4:
            frequency = st.selectbox("Frequency", ["daily", "weekly", "as-needed"])
        with col5:
            start_time = st.text_input("Start time (HH:MM, optional)", value="")
        add_task = st.form_submit_button("Add task")

    if add_task:
        existing = [t.name for t in pet.get_tasks()]
        if task_name in existing:
            st.error(f"'{task_name}' already exists for {pet.name}.")
        else:
            try:
                new_task = Task(
                    name=task_name,
                    duration_minutes=int(duration),
                    priority=priority,
                    frequency=frequency,
                    start_time=start_time.strip() if start_time.strip() else None,
                )
                pet.add_task(new_task)
                st.success(f"Task '{task_name}' added to {pet.name}.")
            except ValueError as e:
                st.error(f"Invalid input: {e}")

    # Task table for the selected pet
    all_tasks = pet.get_tasks()
    if all_tasks:
        st.markdown(f"**{pet.name}'s tasks:**")
        rows = []
        for t in all_tasks:
            rows.append({
                "Status":   "✅ Done" if t.completed else "⬜ Pending",
                "Task":     t.name,
                "Duration": f"{t.duration_minutes} min",
                "Priority": t.priority,
                "Frequency": t.frequency,
                "Start":    t.start_time or "—",
                "Next due": str(t.next_due) if t.next_due else "today",
            })
        st.table(rows)
    else:
        st.info("No tasks yet for this pet.")

st.divider()

# ── Section 4: Conflict check ─────────────────────────────────────────────────
st.subheader("4. Check for conflicts")

if st.session_state.owner and st.session_state.owner.pets:
    scheduler = Scheduler(st.session_state.owner)
    conflicts = scheduler.detect_conflicts()
    if conflicts:
        st.error(f"⚠️ {len(conflicts)} scheduling conflict(s) detected — review before generating your plan:")
        for warning in conflicts:
            st.warning(warning)
    else:
        st.success("No scheduling conflicts detected.")
else:
    st.info("Add pets and tasks to check for conflicts.")

st.divider()

# ── Section 5: Generate schedule ──────────────────────────────────────────────
st.subheader("5. Generate today's schedule")

if st.session_state.owner is None:
    st.warning("Set up your owner info before generating a schedule.")
elif not st.session_state.owner.pets:
    st.warning("Add at least one pet and one task before generating a schedule.")
else:
    sort_mode = st.radio(
        "Sort tasks by",
        ["Priority (recommended)", "Duration — shortest first", "Weighted score"],
        horizontal=True,
        help=(
            "**Priority** — high → medium → low, shorter first within same priority.\n\n"
            "**Duration** — shortest tasks first regardless of priority.\n\n"
            "**Weighted score** — blends priority urgency, recurrence frequency, and "
            "duration efficiency into one numeric rank. Daily high-priority short tasks "
            "score highest; as-needed low-priority long tasks score lowest."
        ),
    )

    if st.button("Generate schedule"):
        scheduler = Scheduler(st.session_state.owner)
        all_pending = scheduler.get_all_tasks()

        if sort_mode == "Duration — shortest first":
            sorted_tasks = scheduler.sort_by_duration(all_pending)
        elif sort_mode == "Weighted score":
            sorted_tasks = scheduler.sort_by_weight(all_pending)
        else:
            sorted_tasks = scheduler.sort_by_priority(all_pending)

        scheduled, skipped = scheduler.filter_by_time(sorted_tasks)

        if not all_pending:
            st.info("All tasks are already complete or none are due today.")
        else:
            # Summary metric row
            time_used = sum(t.duration_minutes for t in scheduled)
            time_left = st.session_state.owner.available_minutes - time_used
            c1, c2, c3 = st.columns(3)
            c1.metric("Tasks scheduled", len(scheduled))
            c2.metric("Minutes used", f"{time_used} min")
            c3.metric("Time remaining", f"{time_left} min")

            # Scheduled table
            if scheduled:
                st.markdown("#### Scheduled tasks")
                sched_rows = []
                for t in scheduled:
                    sched_rows.append({
                        "Task":      t.name,
                        "Priority":  t.priority,
                        "Duration":  f"{t.duration_minutes} min",
                        "Frequency": t.frequency,
                        "Start":     t.start_time or "—",
                    })
                st.table(sched_rows)
            else:
                st.warning("No tasks fit within your available time.")

            # Skipped table
            if skipped:
                with st.expander(f"Skipped tasks ({len(skipped)} — not enough time)"):
                    skip_rows = [
                        {
                            "Task":     t.name,
                            "Priority": t.priority,
                            "Duration": f"{t.duration_minutes} min",
                        }
                        for t in skipped
                    ]
                    st.table(skip_rows)

            # Conflict warnings surfaced again in the schedule view
            conflicts = scheduler.detect_conflicts()
            if conflicts:
                st.markdown("#### Scheduling warnings")
                for warning in conflicts:
                    st.warning(warning)

            # Reasoning
            with st.expander("Why was the plan built this way?"):
                pet_count = len(st.session_state.owner.pets)
                if sort_mode.startswith("Duration"):
                    mode_label = "duration (shortest first)"
                elif sort_mode.startswith("Weighted"):
                    mode_label = "weighted score (priority + frequency + efficiency)"
                else:
                    mode_label = "priority (high → medium → low)"
                st.info(
                    f"Retrieved {len(all_pending)} pending task(s) across {pet_count} pet(s). "
                    f"Tasks were sorted by {mode_label}. "
                    f"{len(scheduled)} task(s) fit within "
                    f"{st.session_state.owner.available_minutes} available minutes; "
                    f"{len(skipped)} task(s) were skipped due to time constraints."
                )
