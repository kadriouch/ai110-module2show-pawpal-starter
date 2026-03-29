import streamlit as st
from pawpal_system import Owner, Pet, Task, Scheduler

st.set_page_config(page_title="PawPal+", page_icon="🐾", layout="centered")

# --- Session state initialisation ---
# Streamlit reruns the entire script on every interaction.
# We guard each key with "not in" so objects are created once and then
# kept alive in st.session_state for the rest of the session.
if "owner" not in st.session_state:
    st.session_state.owner = None          # set after the owner form is submitted
if "current_pet" not in st.session_state:
    st.session_state.current_pet = None    # the pet whose tasks we are editing

# ── Title ────────────────────────────────────────────────────────────────────
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
            "Time available today (minutes)", min_value=5, max_value=480, value=60, step=5
        )
    submitted = st.form_submit_button("Save owner")

if submitted:
    if st.session_state.owner is None:
        # First save — create the Owner and carry over any pets added earlier
        st.session_state.owner = Owner(name=owner_name, available_minutes=int(available_minutes))
    else:
        # Owner already exists — just update name and time budget
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
            st.session_state.owner.add_pet(new_pet)         # → Owner.add_pet()
            st.session_state.current_pet = new_pet
            st.success(f"Added {species} '{pet_name}'!")

    # Show registered pets and let user pick which one to add tasks to
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
            duration = st.number_input(
                "Duration (min)", min_value=1, max_value=240, value=20
            )
        with col3:
            priority = st.selectbox("Priority", ["high", "medium", "low"])
        frequency = st.selectbox("Frequency", ["daily", "weekly", "as-needed"])
        add_task = st.form_submit_button("Add task")

    if add_task:
        existing = [t.name for t in pet.get_tasks()]
        if task_name in existing:
            st.error(f"'{task_name}' already exists for {pet.name}.")
        else:
            new_task = Task(
                name=task_name,
                duration_minutes=int(duration),
                priority=priority,
                frequency=frequency,
            )
            pet.add_task(new_task)                           # → Pet.add_task()
            st.success(f"Task '{task_name}' added to {pet.name}.")

    # Show all tasks for the selected pet
    all_tasks = pet.get_tasks()
    if all_tasks:
        st.markdown(f"**{pet.name}'s tasks:**")
        for t in all_tasks:
            status = "✅" if t.completed else "⬜"
            st.markdown(
                f"{status} **{t.name}** — {t.duration_minutes} min | "
                f"priority: `{t.priority}` | frequency: `{t.frequency}`"
            )
    else:
        st.info("No tasks yet for this pet.")

st.divider()

# ── Section 4: Generate schedule ──────────────────────────────────────────────
st.subheader("4. Generate today's schedule")

if st.session_state.owner is None:
    st.warning("Set up your owner info before generating a schedule.")
elif not st.session_state.owner.pets:
    st.warning("Add at least one pet and one task before generating a schedule.")
else:
    if st.button("Generate schedule"):
        scheduler = Scheduler(st.session_state.owner)       # → Scheduler(owner)
        plan = scheduler.generate_plan()                    # → Scheduler.generate_plan()

        st.success(f"Plan generated — {plan.total_duration} min scheduled.")

        if plan.scheduled_tasks:
            st.markdown("### Scheduled tasks")
            for task in plan.scheduled_tasks:
                st.markdown(
                    f"- **{task.name}** — {task.duration_minutes} min | `{task.priority}` priority"
                )
        else:
            st.warning("No tasks fit within your available time.")

        if plan.skipped_tasks:
            st.markdown("### Skipped (not enough time)")
            for task in plan.skipped_tasks:
                st.markdown(
                    f"- {task.name} — {task.duration_minutes} min | `{task.priority}` priority"
                )

        st.markdown("### Reasoning")
        st.info(plan.explanation)
