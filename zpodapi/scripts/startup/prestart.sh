python wait_for_db.py
cd ../alembic
alembic upgrade head
cd - > /dev/null
python load_initial_data.py
