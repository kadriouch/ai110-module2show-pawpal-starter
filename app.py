import streamlit as st
from pawpal_system import Owner, Pet, Task, Scheduler

st.set_page_config(page_title="PawPal+", page_icon="🐾", layout="wide")

DATA_FILE = "data.json"

# ── Emoji / label helpers ─────────────────────────────────────────────────────

PRIORITY_EMOJI  = {"high": "🔴", "medium": "🟡", "low": "🟢"}
FREQUENCY_EMOJI = {"daily": "📅", "weekly": "📆", "as-needed": "🔔"}
SPECIES_EMOJI   = {"dog": "🐕", "cat": "🐈", "rabbit": "🐰", "bird": "🐦", "other": "🐾"}

# Keyword → emoji for auto-tagging task names
TASK_KEYWORDS = [
    ({"walk", "run", "jog", "hike", "exercise"},          "🦮"),
    ({"feed", "food", "meal", "eat", "breakfast", "dinner", "lunch"}, "🍖"),
    ({"med", "medication", "medicine", "pill", "tablet", "dose"},     "💊"),
    ({"groom", "brush", "bath", "wash", "trim", "nail"},              "✂️"),
    ({"play", "toy", "fetch", "laser", "enrich"},                     "🎾"),
    ({"vet", "check", "appointment", "clinic"},                        "🏥"),
    ({"water", "drink"},                                               "💧"),
    ({"train", "training", "teach", "command"},                        "🎓"),
]

def task_icon(name: str) -> str:
    """Return an emoji based on keywords found in the task name."""
    lower = name.lower()
    for keywords, icon in TASK_KEYWORDS:
        if any(kw in lower for kw in keywords):
            return icon
    return "📌"

def priority_label(priority: str) -> str:
    return f"{PRIORITY_EMOJI.get(priority, '')} {priority.capitalize()}"

def species_label(species: str) -> str:
    return f"{SPECIES_EMOJI.get(species, '🐾')} {species.capitalize()}"

def save():
    """Persist current owner state to disk."""
    if st.session_state.owner:
        st.session_state.owner.save_to_json(DATA_FILE)

# ── Session state ─────────────────────────────────────────────────────────────
if "owner" not in st.session_state:
    st.session_state.owner = Owner.load_from_json(DATA_FILE)
if "current_pet" not in st.session_state:
    st.session_state.current_pet = None

if (
    st.session_state.owner
    and st.session_state.current_pet is None
    and st.session_state.owner.pets
):
    st.session_state.current_pet = st.session_state.owner.pets[0]

# ── Sidebar overview ──────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("## 🐾 PawPal+")
    st.caption("Your daily pet care planner")
    st.divider()

    owner = st.session_state.owner
    if owner:
        st.markdown(f"**👤 {owner.name}**")
        pending_total = sum(len(p.get_pending_tasks()) for p in owner.pets)
        done_total    = sum(
            len([t for t in p.get_tasks() if t.completed]) for p in owner.pets
        )
        st.caption(f"{pending_total} task(s) pending · {done_total} done today")

        # Time budget bar
        st.markdown("**⏱ Time budget**")
        st.progress(
            min(1.0, (owner.available_minutes) / 480),
            text=f"{owner.available_minutes} min available"
        )

        st.divider()
        if owner.pets:
            st.markdown("**Your pets**")
            for pet in owner.pets:
                pending = len(pet.get_pending_tasks())
                total   = len(pet.get_tasks())
                icon    = SPECIES_EMOJI.get(pet.species, "🐾")
                st.markdown(f"{icon} **{pet.name}** — {pending}/{total} tasks pending")
        else:
            st.caption("No pets yet.")
    else:
        st.caption("Set up your owner profile to get started.")

# ── Title ─────────────────────────────────────────────────────────────────────
st.title("🐾 PawPal+")
st.caption("Your daily pet care planner")
st.divider()

# ── Section 1: Owner setup ────────────────────────────────────────────────────
st.subheader("👤 1. Owner setup")

with st.form("owner_form"):
    col1, col2 = st.columns(2)
    with col1:
        owner_name = st.text_input("Your name", value="Jordan")
    with col2:
        available_minutes = st.number_input(
            "Time available today (minutes)", min_value=0, max_value=480, value=60, step=5
        )
    submitted = st.form_submit_button("💾 Save owner")

if submitted:
    if st.session_state.owner is None:
        st.session_state.owner = Owner(name=owner_name, available_minutes=int(available_minutes))
    else:
        st.session_state.owner.name = owner_name
        st.session_state.owner.set_available_time(int(available_minutes))
    save()
    st.success(f"✅ Owner '{owner_name}' saved — {available_minutes} min available today.")

if st.session_state.owner:
    st.info(
        f"👤 **{st.session_state.owner.name}** · "
        f"⏱ {st.session_state.owner.available_minutes} min available today"
    )

st.divider()

# ── Section 2: Add a pet ──────────────────────────────────────────────────────
st.subheader("🐾 2. Add a pet")

if st.session_state.owner is None:
    st.warning("Please save your owner info above before adding pets.")
else:
    with st.form("pet_form"):
        col1, col2 = st.columns(2)
        with col1:
            pet_name = st.text_input("Pet name", value="Mochi")
        with col2:
            species = st.selectbox("Species", ["dog", "cat", "rabbit", "bird", "other"],
                                   format_func=species_label)
        add_pet = st.form_submit_button("➕ Add pet")

    if add_pet:
        existing_names = [p.name for p in st.session_state.owner.pets]
        if pet_name in existing_names:
            st.error(f"A pet named '{pet_name}' already exists.")
        else:
            new_pet = Pet(name=pet_name, species=species)
            st.session_state.owner.add_pet(new_pet)
            st.session_state.current_pet = new_pet
            save()
            st.success(f"✅ Added {species_label(species)} **{pet_name}**!")

    if st.session_state.owner.pets:
        pet_options = {p.name: p for p in st.session_state.owner.pets}
        selected = st.selectbox(
            "Select a pet to manage tasks for",
            list(pet_options.keys()),
            format_func=lambda n: f"{SPECIES_EMOJI.get(pet_options[n].species, '🐾')} {n}",
        )
        st.session_state.current_pet = pet_options[selected]
    else:
        st.info("No pets yet. Add one above.")

st.divider()

# ── Section 3: Add tasks ──────────────────────────────────────────────────────
st.subheader("📋 3. Add care tasks")

if st.session_state.owner is None or not st.session_state.owner.pets:
    st.warning("Add a pet first before adding tasks.")
elif st.session_state.current_pet is None:
    st.warning("Select a pet above to add tasks to.")
else:
    pet = st.session_state.current_pet
    icon = SPECIES_EMOJI.get(pet.species, "🐾")
    st.markdown(f"Adding tasks for **{icon} {pet.name}** ({pet.species})")

    with st.form("task_form"):
        col1, col2, col3 = st.columns(3)
        with col1:
            task_name = st.text_input("Task name", value="Morning walk",
                                      help="Keywords like 'walk', 'feed', 'medication' auto-assign an icon.")
        with col2:
            duration = st.number_input("Duration (min)", min_value=1, max_value=240, value=20)
        with col3:
            priority = st.selectbox("Priority", ["high", "medium", "low"],
                                    format_func=priority_label)
        col4, col5 = st.columns(2)
        with col4:
            frequency = st.selectbox("Frequency", ["daily", "weekly", "as-needed"])
        with col5:
            start_time = st.text_input("Start time (HH:MM, optional)", value="")
        add_task = st.form_submit_button("➕ Add task")

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
                save()
                st.success(f"✅ {task_icon(task_name)} **{task_name}** added to {icon} {pet.name}.")
            except ValueError as e:
                st.error(f"Invalid input: {e}")

    all_tasks = pet.get_tasks()
    if all_tasks:
        st.markdown(f"**{icon} {pet.name}'s tasks**")
        rows = []
        for t in all_tasks:
            rows.append({
                "":          task_icon(t.name),
                "Status":    "✅ Done" if t.completed else "⬜ Pending",
                "Task":      t.name,
                "Priority":  priority_label(t.priority),
                "Duration":  f"{t.duration_minutes} min",
                "Frequency": f"{FREQUENCY_EMOJI.get(t.frequency, '')} {t.frequency}",
                "Start":     t.start_time or "—",
                "Next due":  str(t.next_due) if t.next_due else "today",
            })
        st.dataframe(rows, use_container_width=True, hide_index=True)
    else:
        st.info("No tasks yet for this pet.")

st.divider()

# ── Section 4: Conflict check ─────────────────────────────────────────────────
st.subheader("⚠️ 4. Conflict check")

if st.session_state.owner and st.session_state.owner.pets:
    scheduler = Scheduler(st.session_state.owner)
    conflicts = scheduler.detect_conflicts()
    if conflicts:
        st.error(f"⚠️ {len(conflicts)} scheduling conflict(s) detected — review before generating your plan:")
        for warning in conflicts:
            st.warning(f"🔶 {warning}")
    else:
        st.success("✅ No scheduling conflicts detected.")
else:
    st.info("Add pets and tasks to check for conflicts.")

st.divider()

# ── Section 5: Generate schedule ──────────────────────────────────────────────
st.subheader("📅 5. Generate today's schedule")

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
            "**Priority** — 🔴 high → 🟡 medium → 🟢 low, shorter first within same priority.\n\n"
            "**Duration** — shortest tasks first regardless of priority.\n\n"
            "**Weighted score** — blends priority urgency, recurrence frequency, and "
            "duration efficiency into one numeric rank."
        ),
    )

    if st.button("🗓 Generate schedule", type="primary"):
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
            st.info("🎉 All tasks are already complete or none are due today.")
        else:
            time_used = sum(t.duration_minutes for t in scheduled)
            budget    = st.session_state.owner.available_minutes
            time_left = budget - time_used
            pct_used  = time_used / budget if budget > 0 else 0.0

            # Metric row
            c1, c2, c3, c4 = st.columns(4)
            c1.metric("✅ Scheduled",    len(scheduled))
            c2.metric("⏩ Skipped",      len(skipped))
            c3.metric("⏱ Minutes used",  f"{time_used} min")
            c4.metric("💚 Time left",    f"{time_left} min")

            # Time budget progress bar
            bar_color = "normal" if pct_used <= 0.8 else "error" if pct_used >= 1.0 else "warning"
            st.progress(min(1.0, pct_used), text=f"{time_used}/{budget} min used ({pct_used:.0%})")

            # Scheduled tasks
            if scheduled:
                st.markdown("#### ✅ Scheduled tasks")
                sched_rows = []
                for t in scheduled:
                    sched_rows.append({
                        "":          task_icon(t.name),
                        "Task":      t.name,
                        "Priority":  priority_label(t.priority),
                        "Duration":  f"{t.duration_minutes} min",
                        "Frequency": f"{FREQUENCY_EMOJI.get(t.frequency, '')} {t.frequency}",
                        "Start":     t.start_time or "—",
                    })
                st.dataframe(sched_rows, use_container_width=True, hide_index=True)
            else:
                st.warning("⚠️ No tasks fit within your available time.")

            # Skipped tasks
            if skipped:
                with st.expander(f"⏩ Skipped tasks ({len(skipped)} — insufficient time)"):
                    skip_rows = [
                        {
                            "":         task_icon(t.name),
                            "Task":     t.name,
                            "Priority": priority_label(t.priority),
                            "Duration": f"{t.duration_minutes} min",
                        }
                        for t in skipped
                    ]
                    st.dataframe(skip_rows, use_container_width=True, hide_index=True)

            # Conflict warnings in plan view
            conflicts = scheduler.detect_conflicts()
            if conflicts:
                st.markdown("#### 🔶 Scheduling warnings")
                for w in conflicts:
                    st.warning(f"🔶 {w}")

            # Reasoning
            with st.expander("🧠 Why was the plan built this way?"):
                pet_count = len(st.session_state.owner.pets)
                if sort_mode.startswith("Duration"):
                    mode_label = "duration (shortest first)"
                elif sort_mode.startswith("Weighted"):
                    mode_label = "weighted score (priority + frequency + efficiency)"
                else:
                    mode_label = "priority (🔴 high → 🟡 medium → 🟢 low)"
                st.info(
                    f"Retrieved **{len(all_pending)}** pending task(s) across "
                    f"**{pet_count}** pet(s). "
                    f"Tasks were sorted by **{mode_label}**. "
                    f"**{len(scheduled)}** task(s) fit within "
                    f"**{budget} min** of available time; "
                    f"**{len(skipped)}** task(s) were skipped due to time constraints."
                )
