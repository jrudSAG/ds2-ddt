import os
import shutil
from typing import Dict
import great_expectations as gx
from config import ConfigLoader
from utils.utils import topic_url_to_name

class GXInitializer:
    """
    Initializes the Great Expectations context, data source, expectation suites, and validation definitions
    based on a configuration file.
    """
    def __init__(self, gx_root_dir: str = './validation'):
        self.gx_root_dir = gx_root_dir
        self.config_name = 'generated_validation_config.json'
        self.context = None
        self.suites: Dict[str, gx.ExpectationSuite] = {}
        self.validation_definitions: Dict[str, gx.ValidationDefinition] = {}
        
        # Delete existing gx folder for a fresh start.
        self._check_and_delete_gx_folder()
        # Initialize the GE context.
        self._initialize_context()
        # Load validation configuration from JSON.
        self._load_validation_config()
        # Create a data source and asset for MQTT data.
        self._create_data_source()
        # Create expectation suites for each topic.
        self._create_expectation_suites()
        # Add expectations to each suite based on the config.
        self._add_expectations_to_suites()
        # Create validation definitions linking data and expectation suites.
        self._create_validation_definitions()
        
    def _check_and_delete_gx_folder(self):
        gx_folder_path = os.path.join(self.gx_root_dir, 'gx')
        if os.path.exists(gx_folder_path):
            shutil.rmtree(gx_folder_path)

    def _initialize_context(self):
        self.context = gx.get_context(mode='file', project_root_dir=self.gx_root_dir)

    def _load_validation_config(self):
        config_loader = ConfigLoader()
        self.validation_config = config_loader.load_config(self.config_name)

    def _create_data_source(self):
        data_source_name = "pandas-data-source"
        self.data_source = self.context.data_sources.add_pandas(name=data_source_name)

        data_asset_name = "mqtt-data-asset"
        self.data_asset = self.data_source.add_dataframe_asset(name=data_asset_name)

        batch_definition_name = "mqtt-batch"
        self.batch_definition = self.data_asset.add_batch_definition_whole_dataframe(batch_definition_name)

    def _create_expectation_suites(self):
        for topic in self.validation_config['validations']:
            suite_name = f"{topic_url_to_name(topic)}_expectation_suite"
            suite = gx.ExpectationSuite(name=suite_name)
            self.suites[topic] = self.context.suites.add(suite)

    def _add_expectations_to_suites(self):
        expectation_mapping = {
            "expect_column_values_to_be_between": gx.expectations.ExpectColumnValuesToBeBetween,
            "expect_column_pair_values_a_to_be_greater_than_b": gx.expectations.ExpectColumnPairValuesAToBeGreaterThanB,
            "expect_column_values_to_be_in_set": gx.expectations.ExpectColumnValuesToBeInSet,
            "expect_column_values_to_match_regex": gx.expectations.ExpectColumnValuesToMatchRegex,
            "expect_column_values_to_not_match_regex": gx.expectations.ExpectColumnValuesToNotMatchRegex,
            "expect_column_values_to_match_regex_list": gx.expectations.ExpectColumnValuesToMatchRegexList,
            "expect_column_values_to_not_match_regex_list": gx.expectations.ExpectColumnValuesToNotMatchRegexList,
            "expect_column_values_to_be_unique": gx.expectations.ExpectColumnValuesToBeUnique,
            "expect_column_values_to_not_be_null": gx.expectations.ExpectColumnValuesToNotBeNull,
            "expect_column_values_to_be_null": gx.expectations.ExpectColumnValuesToBeNull,
            "expect_column_values_to_match_json_schema": gx.expectations.ExpectColumnValuesToMatchJsonSchema,
            "expect_column_values_to_be_of_type": gx.expectations.ExpectColumnValuesToBeOfType,
            "expect_column_values_to_be_in_type_list": gx.expectations.ExpectColumnValuesToBeInTypeList,
            "expect_column_pair_values_to_be_equal": gx.expectations.ExpectColumnPairValuesToBeEqual,
            "expect_column_pair_values_to_be_in_set": gx.expectations.ExpectColumnPairValuesToBeInSet,
            "expect_table_row_count_to_be_between": gx.expectations.ExpectTableRowCountToBeBetween,
            "expect_table_row_count_to_equal": gx.expectations.ExpectTableRowCountToEqual,
            "expect_table_column_count_to_be_between": gx.expectations.ExpectTableColumnCountToBeBetween,
            "expect_table_column_count_to_equal": gx.expectations.ExpectTableColumnCountToEqual,
            "expect_table_columns_to_match_ordered_list": gx.expectations.ExpectTableColumnsToMatchOrderedList,
            "expect_table_columns_to_match_set": gx.expectations.ExpectTableColumnsToMatchSet,
            "expect_column_kl_divergence_to_be_less_than": gx.expectations.ExpectColumnKLDivergenceToBeLessThan,
            "expect_column_max_to_be_between": gx.expectations.ExpectColumnMaxToBeBetween,
            "expect_column_mean_to_be_between": gx.expectations.ExpectColumnMeanToBeBetween,
            "expect_column_median_to_be_between": gx.expectations.ExpectColumnMedianToBeBetween,
            "expect_column_most_common_value_to_be_in_set": gx.expectations.ExpectColumnMostCommonValueToBeInSet,
            "expect_column_stdev_to_be_between": gx.expectations.ExpectColumnStdevToBeBetween,
            "expect_column_min_to_be_between": gx.expectations.ExpectColumnMinToBeBetween,
            "expect_column_values_to_not_be_in_set": gx.expectations.ExpectColumnValuesToNotBeInSet,
        }

        for topic, attributes in self.validation_config['validations'].items():
            suite: gx.ExpectationSuite = self.suites[topic]
            for attribute, expectations in attributes.items():
                for expectation in expectations:
                    rule = expectation['rule']
                    params = expectation['params']
    
                    expectation_class = expectation_mapping.get(rule)
                    if expectation_class:
            
                        expectation_obj = expectation_class(**params)
         
                        suite.add_expectation(expectation_obj)

    def _create_validation_definitions(self):

        for topic in self.validation_config['validations']:
            definition_name = f"{topic_url_to_name(topic)}_validation_definition"
            validation_definition = gx.ValidationDefinition(
                data=self.batch_definition,
                suite=self.suites[topic],
                name=definition_name
            )
            self.validation_definitions[topic] = self.context.validation_definitions.add(validation_definition)
