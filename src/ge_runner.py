import enum
from datetime import datetime
from typing import Dict, Any, List, Optional, Literal

from great_expectations.data_context.data_context import DataContext
from great_expectations.core.batch import RuntimeBatchRequest

@enum.unique
class RunMode(enum.Enum):
    local = "local"
    aws = "aws"

    def __str__(self) -> str:
        return str(self.value)

class GeRunner:
    def __init__(
        self,
        run_mode: Literal["local", "aws"],
        connection_str: str,
        aws_access_key: str,
        aws_secret_key: str,
        region: str,
        aws_token: str
    ) -> None:
        if RunMode(run_mode) == RunMode.aws:
            self.__checkpoint = "aws_checkpoint"
            validations_store_name = "validations_s3_store"
        else:
            self.__checkpoint = "local_checkpoint"
            validations_store_name = "validations_store"

        runtime_environment = {
            "connection_str": connection_str,
            "deployment_bucket": "store_bucket",
            "datadocs_bucket": "datadocs_bucket",
            "access_key_id": aws_access_key,
            "secret_access_key": aws_secret_key,
            "session_token": aws_token,
            "aws_region_name": region,
            "validations_store_name": validations_store_name,
        }

        self.__context = DataContext(runtime_environment=runtime_environment)
        
    def validate_tables(self, tables_to_validate: List[Dict]) -> Dict[str, Any]:
        validations = []

        for table_to_validate in tables_to_validate:
            schema=table_to_validate["schema"] if "schema" in table_to_validate else None
            validation = self._get_table_validation(table=table_to_validate["table"], schema=schema, expectation_suite_name=table_to_validate["suite"])
            validations.append(validation)

        result = self.__context.run_checkpoint(
            run_name=f"validate_tables_{datetime.now().strftime('%Y%m%d%H%M')}",
            checkpoint_name=self.__checkpoint,
            validations=validations,
        )
        return result.to_json_dict()

    def _get_table_validation(self, table: str, schema: Optional[str], expectation_suite_name: str):
        batch_request_dict = self._runtime_batch_request(table=table, schema=schema).to_json_dict()
        return {"batch_request": batch_request_dict, "expectation_suite_name": expectation_suite_name}

    def _runtime_batch_request(self, table: str, schema: Optional[str]) -> RuntimeBatchRequest:
        if schema:
            table_name = f"{schema}.{table}"
            batch_spec_passthrough = {"create_temp_table": False, "table_name": table, "schema_name": schema}
        else:
            table_name = table
            batch_spec_passthrough = {"create_temp_table": False, "table_name": table}

        return RuntimeBatchRequest(
            datasource_name="rs_datasource",
            data_connector_name="main_dataconnector",
            data_asset_name=table_name,
            runtime_parameters={"query": f"(select * from {table_name})"},
            batch_identifiers={"batch_id": "sample_batch"},
            batch_spec_passthrough=batch_spec_passthrough,
        )