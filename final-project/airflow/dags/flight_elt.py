from airflow.sdk import dag, task
from datetime import datetime, timedelta
import pendulum
import requests
import clickhouse_connect

@dag(
    dag_id="flight_elt",
    start_date=pendulum.datetime(2026, 9, 1, tz="Asia/Jakarta"),
    schedule="0 * * * *",
    catchup=False,
    tags=["flight", "opensky"],
)
def flight_elt():

    @task
    def extract():
        import requests
        from requests.adapters import HTTPAdapter
        from urllib3.util.retry import Retry

        url = "https://opensky-network.org/api/states/all"

        session = requests.Session()

        retry = Retry(
            total=3,
            backoff_factor=2,
            status_forcelist=[429, 500, 502, 503, 504],
            allowed_methods=["GET"],
        )

        session.mount("https://", HTTPAdapter(max_retries=retry))

        response = session.get(url, timeout=60)
        response.raise_for_status()

        data = response.json()

        print(f"Jumlah data API: {len(data.get('states', []))}")

        return data["states"]
    

    @task
    def load(states):

        client = clickhouse_connect.get_client(
            host="host.docker.internal",
            port=8124,
            username="default",
            password="admin123",
            database="flight",
        )

        rows = []

        for state in states:
            if state[4] is None:
                continue

            rows.append(
                [
                    datetime.fromtimestamp(state[4]),
                    state[0],
                    state[1].strip() if state[1] else "",
                    state[2],
                    state[5],
                    state[6],
                    state[7],
                    state[13],
                    state[9],
                    state[10],
                    state[11],
                    1 if state[8] else 0,
                ]
            )

        client.insert(
            "raw_flights",
            rows,
            column_names=[
                "event_time",
                "icao24",
                "callsign",
                "origin_country",
                "longitude",
                "latitude",
                "baro_altitude",
                "geo_altitude",
                "velocity",
                "heading",
                "vertical_rate",
                "on_ground",
            ],
        )

        print(f"Inserted {len(rows)} rows")

    @task
    def run_dbt():
        import subprocess

        result = subprocess.run(
            [
                "dbt",
                "run",
                "--project-dir",
                "/opt/airflow/flight_dbt",
                "--profiles-dir",
                "/home/airflow/.dbt",
                "--target",
                "airflow",
            ],
            capture_output=True,
            text=True,
        )

        print(result.stdout)

        if result.returncode != 0:
            print(result.stderr)
            raise Exception("dbt run gagal")

    states = extract()

    load_task = load(states)

    run_dbt_task = run_dbt()

    load_task >> run_dbt_task


flight_elt()
