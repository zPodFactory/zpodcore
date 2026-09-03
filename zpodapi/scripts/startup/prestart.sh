python wait_for_db.py
cd ../alembic
alembic upgrade head
cd - > /dev/null
python zpodfactory_load_initial_data.py
python zpodfactory_load_default_settings.py
