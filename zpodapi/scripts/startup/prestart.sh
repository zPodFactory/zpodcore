python wait_for_db.py
cd ../alembic
if ! alembic upgrade head; then
    echo "ERROR: the database migration failed (see above). Fix the cause, then run" >&2
    echo "ERROR: \`just alembic-upgrade\` and restart zpodapi." >&2
    exit 1
fi
cd - > /dev/null
python zpodfactory_load_initial_data.py
python zpodfactory_load_default_settings.py
