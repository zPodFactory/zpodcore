#!/usr/bin/env bash
# Wrapper around the official postgres entrypoint.
#
# Postgres records, per database, the glibc collation version it was created
# with. When the base image moves to a newer Debian (bullseye 2.31 -> trixie
# 2.41), an existing volume logs "collation version mismatch" on every
# connection, and text indexes built under the old rules may be inconsistent.
# The fix is REINDEX DATABASE + ALTER DATABASE ... REFRESH COLLATION VERSION,
# once per database. This wrapper does that on a temporary, socket-only
# server before the real one starts, so no client ever sees the mismatch.
set -Eeo pipefail

# Gives us docker_setup_env, docker_temp_server_start/stop, etc. The official
# script only runs its _main when executed, not when sourced.
source /usr/local/bin/docker-entrypoint.sh

if [ "$1" = 'postgres' ] && ! _pg_want_help "$@"; then
	docker_setup_env
	docker_create_db_directories
	if [ "$(id -u)" = '0' ]; then
		exec gosu postgres "$BASH_SOURCE" "$@"
	fi

	# Fresh volume: nothing to check, the official init creates the databases.
	if [ -n "$DATABASE_ALREADY_EXISTS" ]; then
		docker_temp_server_start "$@"

		psql_pg() { psql -v ON_ERROR_STOP=1 --username postgres --no-password -qtA "$@"; }

		mismatched="$(psql_pg --dbname postgres -c "
			SELECT datname FROM pg_database
			WHERE datallowconn
			  AND datcollversion IS DISTINCT FROM pg_database_collation_actual_version(oid)
			ORDER BY datname")"

		if [ -z "$mismatched" ]; then
			echo "zpodpostgres: collation versions match, nothing to do"
		else
			for db in $mismatched; do
				echo "zpodpostgres: collation version changed for '$db', reindexing"
				psql_pg --dbname "$db" -c "REINDEX DATABASE \"$db\""
				psql_pg --dbname "$db" -c "ALTER DATABASE \"$db\" REFRESH COLLATION VERSION"
			done
			echo "zpodpostgres: collation refresh done"
		fi

		docker_temp_server_stop
	fi
fi

exec docker-entrypoint.sh "$@"
