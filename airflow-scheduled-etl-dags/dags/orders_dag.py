"""The Airflow DAG of the orders pipeline.

The file is a real Airflow DAG: `airflow` is imported at the top, so the file
is only loaded when Airflow is there. The local runner in `src/pipeline.py`
reads the same graph from `src/pipeline.py`, so the pipeline runs without
Airflow installed.

To use it with Airflow:

    export AIRFLOW_HOME=~/airflow
    airflow db init
    cp dags/orders_dag.py $AIRFLOW_HOME/dags/
    airflow dags list
"""

from datetime import datetime, timedelta

try:  # pragma: no cover - only used when Airflow is installed
    from airflow import DAG
    from airflow.operators.python import PythonOperator

    AIRFLOW_INSTALLED = True
except ImportError:  # pragma: no cover - the project runs without Airflow
    DAG = None
    PythonOperator = None
    AIRFLOW_INSTALLED = False


DAG_ID = "orders_etl"
SCHEDULE = "@daily"

#: The tasks of the DAG, and what each of them needs.
TASKS = {
    "extract_orders": [],
    "validate_orders": ["extract_orders"],
    "build_daily": ["validate_orders"],
    "load_warehouse": ["build_daily"],
}


def orders_dag():
    """The DAG of the orders pipeline.

    Every task runs the matching function of the pipeline, so the Airflow run
    and the local run do the same work.
    """
    if not AIRFLOW_INSTALLED:
        raise RuntimeError(
            "Airflow is not installed. Install it with `pip install apache-airflow` "
            "to use this DAG, or run the pipeline with `python main.py run`."
        )

    from src.pipeline import build_daily, extract_orders, load_warehouse, validate_orders

    functions = {
        "extract_orders": extract_orders,
        "validate_orders": validate_orders,
        "build_daily": build_daily,
        "load_warehouse": load_warehouse,
    }

    with DAG(
        DAG_ID,
        description="The daily orders pipeline: extract, validate, aggregate and load.",
        schedule_interval=SCHEDULE,
        start_date=datetime(2026, 1, 1),
        catchup=False,
        tags=["etl", "orders"],
    ) as dag:
        previous = None
        for name, needs in TASKS.items():
            task = PythonOperator(
                task_id=name,
                python_callable=functions[name],
                depends_on=needs or None,
                retries=2,
                retry_delay=timedelta(seconds=30),
            )
            if previous is not None and not needs:
                previous >> task
            previous = task

    return dag


#: The DAG, when Airflow is there.
dag = orders_dag() if AIRFLOW_INSTALLED else None
