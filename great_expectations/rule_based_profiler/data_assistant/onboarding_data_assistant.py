from typing import Any, Dict, List, Optional

from great_expectations.execution_engine.execution_engine import MetricDomainTypes
from great_expectations.rule_based_profiler.config import ParameterBuilderConfig
from great_expectations.rule_based_profiler.data_assistant import DataAssistant
from great_expectations.rule_based_profiler.data_assistant.data_assistant import (
    build_map_metric_rule,
)
from great_expectations.rule_based_profiler.domain_builder import (
    CategoricalColumnDomainBuilder,
    ColumnDomainBuilder,
)
from great_expectations.rule_based_profiler.expectation_configuration_builder import (
    DefaultExpectationConfigurationBuilder,
    ExpectationConfigurationBuilder,
)
from great_expectations.rule_based_profiler.helpers.cardinality_checker import (
    CardinalityLimitMode,
)
from great_expectations.rule_based_profiler.parameter_builder import (
    MetricMultiBatchParameterBuilder,
    ParameterBuilder,
    ValueSetMultiBatchParameterBuilder,
)
from great_expectations.rule_based_profiler.rule import Rule
from great_expectations.rule_based_profiler.types import (
    DOMAIN_KWARGS_PARAMETER_FULLY_QUALIFIED_NAME,
    FULLY_QUALIFIED_PARAMETER_NAME_METADATA_KEY,
    FULLY_QUALIFIED_PARAMETER_NAME_SEPARATOR_CHARACTER,
    FULLY_QUALIFIED_PARAMETER_NAME_VALUE_KEY,
    VARIABLES_KEY,
    Domain,
    SemanticDomainTypes,
)
from great_expectations.rule_based_profiler.types.data_assistant_result import (
    DataAssistantResult,
    OnboardingDataAssistantResult,
)
from great_expectations.validator.validator import Validator


class OnboardingDataAssistant(DataAssistant):
    """
    OnboardingDataAssistant provides dataset exploration and validation to help with Great Expectations "Onboarding".
    """

    __alias__: str = "onboarding"

    def __init__(
        self,
        name: str,
        validator: Validator,
    ) -> None:
        super().__init__(
            name=name,
            validator=validator,
        )

    @property
    def expectation_kwargs_by_expectation_type(self) -> Dict[str, Dict[str, Any]]:
        return {
            "expect_table_row_count_to_be_between": {
                "auto": True,
                "profiler_config": None,
            },
            "expect_table_columns_to_match_set": {
                "auto": True,
                "profiler_config": None,
            },
        }

    @property
    def metrics_parameter_builders_by_domain(
        self,
    ) -> Dict[Domain, List[ParameterBuilder]]:
        table_row_count_metric_multi_batch_parameter_builder: ParameterBuilder = DataAssistant.commonly_used_parameter_builders.get_table_row_count_metric_multi_batch_parameter_builder(
            json_serialize=True
        )
        metric_name: str = "table.columns"
        table_columns_metric_multi_batch_parameter_builder: ParameterBuilder = (
            MetricMultiBatchParameterBuilder(
                name=metric_name,
                metric_name=metric_name,
                metric_domain_kwargs=DOMAIN_KWARGS_PARAMETER_FULLY_QUALIFIED_NAME,
                metric_value_kwargs=None,
                enforce_numeric_metric=False,
                replace_nan_with_zero=False,
                reduce_scalar_metric=True,
                evaluation_parameter_builder_configs=None,
                json_serialize=True,
                data_context=None,
            )
        )
        return {
            Domain(domain_type=MetricDomainTypes.TABLE,): [
                table_row_count_metric_multi_batch_parameter_builder,
                table_columns_metric_multi_batch_parameter_builder,
            ],
        }

    @property
    def variables(self) -> Optional[Dict[str, Any]]:
        return None

    @property
    def rules(self) -> Optional[List[Rule]]:
        column_value_uniqueness_rule: Rule = build_map_metric_rule(
            rule_name="column_value_uniqueness_rule",
            expectation_type="expect_column_values_to_be_unique",
            map_metric_name="column_values.unique",
            include_column_names=None,
            exclude_column_names=None,
            include_column_name_suffixes=None,
            exclude_column_name_suffixes=None,
            semantic_type_filter_module_name=None,
            semantic_type_filter_class_name=None,
            include_semantic_types=None,
            exclude_semantic_types=None,
            max_unexpected_values=0,
            max_unexpected_ratio=None,
            min_max_unexpected_values_proportion=9.75e-1,
        )
        column_value_nullity_rule: Rule = build_map_metric_rule(
            rule_name="column_value_nullity_rule",
            expectation_type="expect_column_values_to_be_null",
            map_metric_name="column_values.null",
            include_column_names=None,
            exclude_column_names=None,
            include_column_name_suffixes=None,
            exclude_column_name_suffixes=None,
            semantic_type_filter_module_name=None,
            semantic_type_filter_class_name=None,
            include_semantic_types=None,
            exclude_semantic_types=None,
            max_unexpected_values=0,
            max_unexpected_ratio=None,
            min_max_unexpected_values_proportion=9.75e-1,
        )
        column_value_nonnullity_rule: Rule = build_map_metric_rule(
            rule_name="column_value_nonnullity_rule",
            expectation_type="expect_column_values_to_not_be_null",
            map_metric_name="column_values.nonnull",
            include_column_names=None,
            exclude_column_names=None,
            include_column_name_suffixes=None,
            exclude_column_name_suffixes=None,
            semantic_type_filter_module_name=None,
            semantic_type_filter_class_name=None,
            include_semantic_types=None,
            exclude_semantic_types=None,
            max_unexpected_values=0,
            max_unexpected_ratio=None,
            min_max_unexpected_values_proportion=9.75e-1,
        )
        numeric_columns_rule: Rule = self._build_numeric_columns_rule()
        datetime_columns_rule: Rule = self._build_datetime_columns_rule()
        categorical_columns_rule: Rule = self._build_categorical_columns_rule()

        return [
            column_value_uniqueness_rule,
            column_value_nullity_rule,
            column_value_nonnullity_rule,
            numeric_columns_rule,
            datetime_columns_rule,
            categorical_columns_rule,
        ]

    def _build_data_assistant_result(
        self, data_assistant_result: DataAssistantResult
    ) -> DataAssistantResult:
        return OnboardingDataAssistantResult(
            batch_id_to_batch_identifier_display_name_map=data_assistant_result.batch_id_to_batch_identifier_display_name_map,
            profiler_config=data_assistant_result.profiler_config,
            metrics_by_domain=data_assistant_result.metrics_by_domain,
            expectation_configurations=data_assistant_result.expectation_configurations,
            citation=data_assistant_result.citation,
            execution_time=data_assistant_result.execution_time,
        )

    @staticmethod
    def _build_numeric_columns_rule() -> Rule:
        """
        This method builds "Rule" object focused on emitting "ExpectationConfiguration" objects for numeric columns.
        """

        # Step-1: Instantiate "ColumnDomainBuilder" for selecting numeric columns (but not "ID-type" columns).

        numeric_column_type_domain_builder: ColumnDomainBuilder = ColumnDomainBuilder(
            include_column_names=None,
            exclude_column_names=None,
            include_column_name_suffixes=None,
            exclude_column_name_suffixes=[
                "_id",
            ],
            semantic_type_filter_module_name=None,
            semantic_type_filter_class_name=None,
            include_semantic_types=[
                SemanticDomainTypes.NUMERIC,
            ],
            exclude_semantic_types=[
                SemanticDomainTypes.IDENTIFIER,
            ],
            data_context=None,
        )

        # Step-2: Declare "ParameterBuilder" for every metric of interest.

        column_histogram_metric_multi_batch_parameter_builder_for_metrics: ParameterBuilder = DataAssistant.commonly_used_parameter_builders.get_column_histogram_metric_multi_batch_parameter_builder(
            json_serialize=True
        )
        column_column_quantile_values_metric_multi_batch_parameter_builder_for_metrics: ParameterBuilder = DataAssistant.commonly_used_parameter_builders.get_column_quantile_values_metric_multi_batch_parameter_builder(
            json_serialize=True
        )
        column_min_metric_multi_batch_parameter_builder_for_metrics: ParameterBuilder = DataAssistant.commonly_used_parameter_builders.get_column_min_metric_multi_batch_parameter_builder(
            json_serialize=True
        )
        column_max_metric_multi_batch_parameter_builder_for_metrics: ParameterBuilder = DataAssistant.commonly_used_parameter_builders.get_column_max_metric_multi_batch_parameter_builder(
            json_serialize=True
        )
        column_median_metric_multi_batch_parameter_builder_for_metrics: ParameterBuilder = DataAssistant.commonly_used_parameter_builders.get_column_median_metric_multi_batch_parameter_builder(
            json_serialize=True
        )
        column_mean_metric_multi_batch_parameter_builder_for_metrics: ParameterBuilder = DataAssistant.commonly_used_parameter_builders.get_column_mean_metric_multi_batch_parameter_builder(
            json_serialize=True
        )
        column_standard_deviation_metric_multi_batch_parameter_builder_for_metrics: ParameterBuilder = DataAssistant.commonly_used_parameter_builders.get_column_standard_deviation_metric_multi_batch_parameter_builder(
            json_serialize=True
        )

        # Step-3: Declare "ParameterBuilder" for every "validation" need in "ExpectationConfigurationBuilder" objects.

        column_min_values_range_parameter_builder_for_validations: ParameterBuilder = DataAssistant.commonly_used_parameter_builders.build_numeric_metric_range_multi_batch_parameter_builder(
            metric_name="column.min",
            metric_value_kwargs=None,
            json_serialize=True,
        )
        column_max_values_range_parameter_builder_for_validations: ParameterBuilder = DataAssistant.commonly_used_parameter_builders.build_numeric_metric_range_multi_batch_parameter_builder(
            metric_name="column.max",
            metric_value_kwargs=None,
            json_serialize=True,
        )
        column_quantile_values_range_parameter_builder_for_validations: ParameterBuilder = DataAssistant.commonly_used_parameter_builders.build_numeric_metric_range_multi_batch_parameter_builder(
            metric_name="column.quantile_values",
            metric_value_kwargs={
                "quantiles": f"{VARIABLES_KEY}quantiles",
                "allow_relative_error": f"{VARIABLES_KEY}allow_relative_error",
            },
            json_serialize=True,
        )
        column_median_values_range_parameter_builder_for_validations: ParameterBuilder = DataAssistant.commonly_used_parameter_builders.build_numeric_metric_range_multi_batch_parameter_builder(
            metric_name="column.median",
            metric_value_kwargs=None,
            json_serialize=True,
        )
        column_mean_values_range_parameter_builder_for_validations: ParameterBuilder = DataAssistant.commonly_used_parameter_builders.build_numeric_metric_range_multi_batch_parameter_builder(
            metric_name="column.mean",
            metric_value_kwargs=None,
            json_serialize=True,
        )
        column_standard_deviation_values_range_parameter_builder_for_validations: ParameterBuilder = DataAssistant.commonly_used_parameter_builders.build_numeric_metric_range_multi_batch_parameter_builder(
            metric_name="column.standard_deviation",
            metric_value_kwargs=None,
            json_serialize=True,
        )

        validation_parameter_builder_configs: Optional[List[ParameterBuilderConfig]]

        # Step-4: Pass "validation" "ParameterBuilderConfig" objects to every "DefaultExpectationConfigurationBuilder", responsible for emitting "ExpectationConfiguration" (with specified "expectation_type").

        validation_parameter_builder_configs = [
            ParameterBuilderConfig(
                **column_min_values_range_parameter_builder_for_validations.to_json_dict(),
            ),
        ]
        expect_column_min_to_be_between_expectation_configuration_builder: DefaultExpectationConfigurationBuilder = DefaultExpectationConfigurationBuilder(
            expectation_type="expect_column_min_to_be_between",
            validation_parameter_builder_configs=validation_parameter_builder_configs,
            column=f"{DOMAIN_KWARGS_PARAMETER_FULLY_QUALIFIED_NAME}{FULLY_QUALIFIED_PARAMETER_NAME_SEPARATOR_CHARACTER}column",
            min_value=f"{column_min_values_range_parameter_builder_for_validations.fully_qualified_parameter_name}{FULLY_QUALIFIED_PARAMETER_NAME_SEPARATOR_CHARACTER}{FULLY_QUALIFIED_PARAMETER_NAME_VALUE_KEY}[0]",
            max_value=f"{column_min_values_range_parameter_builder_for_validations.fully_qualified_parameter_name}{FULLY_QUALIFIED_PARAMETER_NAME_SEPARATOR_CHARACTER}{FULLY_QUALIFIED_PARAMETER_NAME_VALUE_KEY}[1]",
            strict_min=f"{VARIABLES_KEY}strict_min",
            strict_max=f"{VARIABLES_KEY}strict_max",
            meta={
                "profiler_details": f"{column_min_values_range_parameter_builder_for_validations.fully_qualified_parameter_name}{FULLY_QUALIFIED_PARAMETER_NAME_SEPARATOR_CHARACTER}{FULLY_QUALIFIED_PARAMETER_NAME_METADATA_KEY}",
            },
        )

        validation_parameter_builder_configs = [
            ParameterBuilderConfig(
                **column_max_values_range_parameter_builder_for_validations.to_json_dict(),
            ),
        ]
        expect_column_max_to_be_between_expectation_configuration_builder: DefaultExpectationConfigurationBuilder = DefaultExpectationConfigurationBuilder(
            expectation_type="expect_column_max_to_be_between",
            validation_parameter_builder_configs=validation_parameter_builder_configs,
            column=f"{DOMAIN_KWARGS_PARAMETER_FULLY_QUALIFIED_NAME}{FULLY_QUALIFIED_PARAMETER_NAME_SEPARATOR_CHARACTER}column",
            min_value=f"{column_max_values_range_parameter_builder_for_validations.fully_qualified_parameter_name}{FULLY_QUALIFIED_PARAMETER_NAME_SEPARATOR_CHARACTER}{FULLY_QUALIFIED_PARAMETER_NAME_VALUE_KEY}[0]",
            max_value=f"{column_max_values_range_parameter_builder_for_validations.fully_qualified_parameter_name}{FULLY_QUALIFIED_PARAMETER_NAME_SEPARATOR_CHARACTER}{FULLY_QUALIFIED_PARAMETER_NAME_VALUE_KEY}[1]",
            strict_min=f"{VARIABLES_KEY}strict_min",
            strict_max=f"{VARIABLES_KEY}strict_max",
            meta={
                "profiler_details": f"{column_max_values_range_parameter_builder_for_validations.fully_qualified_parameter_name}{FULLY_QUALIFIED_PARAMETER_NAME_SEPARATOR_CHARACTER}{FULLY_QUALIFIED_PARAMETER_NAME_METADATA_KEY}",
            },
        )

        validation_parameter_builder_configs = [
            ParameterBuilderConfig(
                **column_min_values_range_parameter_builder_for_validations.to_json_dict(),
            ),
            ParameterBuilderConfig(
                **column_max_values_range_parameter_builder_for_validations.to_json_dict(),
            ),
        ]
        expect_column_values_to_be_between_expectation_configuration_builder: DefaultExpectationConfigurationBuilder = DefaultExpectationConfigurationBuilder(
            expectation_type="expect_column_values_to_be_between",
            validation_parameter_builder_configs=validation_parameter_builder_configs,
            column=f"{DOMAIN_KWARGS_PARAMETER_FULLY_QUALIFIED_NAME}{FULLY_QUALIFIED_PARAMETER_NAME_SEPARATOR_CHARACTER}column",
            min_value=f"{column_min_values_range_parameter_builder_for_validations.fully_qualified_parameter_name}{FULLY_QUALIFIED_PARAMETER_NAME_SEPARATOR_CHARACTER}{FULLY_QUALIFIED_PARAMETER_NAME_VALUE_KEY}[0]",
            max_value=f"{column_max_values_range_parameter_builder_for_validations.fully_qualified_parameter_name}{FULLY_QUALIFIED_PARAMETER_NAME_SEPARATOR_CHARACTER}{FULLY_QUALIFIED_PARAMETER_NAME_VALUE_KEY}[1]",
            mostly=f"{VARIABLES_KEY}mostly",
            strict_min=f"{VARIABLES_KEY}strict_min",
            strict_max=f"{VARIABLES_KEY}strict_max",
            meta={
                "profiler_details": {
                    "column_min_values_range_estimator": f"{column_min_values_range_parameter_builder_for_validations.fully_qualified_parameter_name}{FULLY_QUALIFIED_PARAMETER_NAME_SEPARATOR_CHARACTER}{FULLY_QUALIFIED_PARAMETER_NAME_METADATA_KEY}",
                    "column_max_values_range_estimator": f"{column_max_values_range_parameter_builder_for_validations.fully_qualified_parameter_name}{FULLY_QUALIFIED_PARAMETER_NAME_SEPARATOR_CHARACTER}{FULLY_QUALIFIED_PARAMETER_NAME_METADATA_KEY}",
                },
            },
        )

        validation_parameter_builder_configs = [
            ParameterBuilderConfig(
                **column_quantile_values_range_parameter_builder_for_validations.to_json_dict(),
            ),
        ]
        expect_expect_column_quantile_values_to_be_between_expectation_configuration_builder: DefaultExpectationConfigurationBuilder = DefaultExpectationConfigurationBuilder(
            expectation_type="expect_column_quantile_values_to_be_between",
            validation_parameter_builder_configs=validation_parameter_builder_configs,
            column=f"{DOMAIN_KWARGS_PARAMETER_FULLY_QUALIFIED_NAME}{FULLY_QUALIFIED_PARAMETER_NAME_SEPARATOR_CHARACTER}column",
            quantile_ranges={
                "quantiles": f"{VARIABLES_KEY}quantiles",
                "value_ranges": f"{column_quantile_values_range_parameter_builder_for_validations.fully_qualified_parameter_name}{FULLY_QUALIFIED_PARAMETER_NAME_SEPARATOR_CHARACTER}{FULLY_QUALIFIED_PARAMETER_NAME_VALUE_KEY}",
            },
            allow_relative_error=f"{VARIABLES_KEY}allow_relative_error",
            meta={
                "profiler_details": f"{column_max_values_range_parameter_builder_for_validations.fully_qualified_parameter_name}{FULLY_QUALIFIED_PARAMETER_NAME_SEPARATOR_CHARACTER}{FULLY_QUALIFIED_PARAMETER_NAME_METADATA_KEY}",
            },
        )

        validation_parameter_builder_configs = [
            ParameterBuilderConfig(
                **column_median_values_range_parameter_builder_for_validations.to_json_dict(),
            ),
        ]
        expect_column_median_to_be_between_expectation_configuration_builder: DefaultExpectationConfigurationBuilder = DefaultExpectationConfigurationBuilder(
            expectation_type="expect_column_median_to_be_between",
            validation_parameter_builder_configs=validation_parameter_builder_configs,
            column=f"{DOMAIN_KWARGS_PARAMETER_FULLY_QUALIFIED_NAME}{FULLY_QUALIFIED_PARAMETER_NAME_SEPARATOR_CHARACTER}column",
            min_value=f"{column_median_values_range_parameter_builder_for_validations.fully_qualified_parameter_name}{FULLY_QUALIFIED_PARAMETER_NAME_SEPARATOR_CHARACTER}{FULLY_QUALIFIED_PARAMETER_NAME_VALUE_KEY}[0]",
            max_value=f"{column_median_values_range_parameter_builder_for_validations.fully_qualified_parameter_name}{FULLY_QUALIFIED_PARAMETER_NAME_SEPARATOR_CHARACTER}{FULLY_QUALIFIED_PARAMETER_NAME_VALUE_KEY}[1]",
            strict_min=f"{VARIABLES_KEY}strict_min",
            strict_max=f"{VARIABLES_KEY}strict_max",
            meta={
                "profiler_details": f"{column_median_values_range_parameter_builder_for_validations.fully_qualified_parameter_name}{FULLY_QUALIFIED_PARAMETER_NAME_SEPARATOR_CHARACTER}{FULLY_QUALIFIED_PARAMETER_NAME_METADATA_KEY}",
            },
        )

        validation_parameter_builder_configs = [
            ParameterBuilderConfig(
                **column_mean_values_range_parameter_builder_for_validations.to_json_dict(),
            ),
        ]
        expect_column_mean_to_be_between_expectation_configuration_builder: DefaultExpectationConfigurationBuilder = DefaultExpectationConfigurationBuilder(
            expectation_type="expect_column_mean_to_be_between",
            validation_parameter_builder_configs=validation_parameter_builder_configs,
            column=f"{DOMAIN_KWARGS_PARAMETER_FULLY_QUALIFIED_NAME}{FULLY_QUALIFIED_PARAMETER_NAME_SEPARATOR_CHARACTER}column",
            min_value=f"{column_mean_values_range_parameter_builder_for_validations.fully_qualified_parameter_name}{FULLY_QUALIFIED_PARAMETER_NAME_SEPARATOR_CHARACTER}{FULLY_QUALIFIED_PARAMETER_NAME_VALUE_KEY}[0]",
            max_value=f"{column_mean_values_range_parameter_builder_for_validations.fully_qualified_parameter_name}{FULLY_QUALIFIED_PARAMETER_NAME_SEPARATOR_CHARACTER}{FULLY_QUALIFIED_PARAMETER_NAME_VALUE_KEY}[1]",
            strict_min=f"{VARIABLES_KEY}strict_min",
            strict_max=f"{VARIABLES_KEY}strict_max",
            meta={
                "profiler_details": f"{column_mean_values_range_parameter_builder_for_validations.fully_qualified_parameter_name}{FULLY_QUALIFIED_PARAMETER_NAME_SEPARATOR_CHARACTER}{FULLY_QUALIFIED_PARAMETER_NAME_METADATA_KEY}",
            },
        )

        validation_parameter_builder_configs = [
            ParameterBuilderConfig(
                **column_standard_deviation_values_range_parameter_builder_for_validations.to_json_dict(),
            ),
        ]
        expect_column_standard_deviation_to_be_between_expectation_configuration_builder: DefaultExpectationConfigurationBuilder = DefaultExpectationConfigurationBuilder(
            expectation_type="expect_column_standard_deviation_to_be_between",
            validation_parameter_builder_configs=validation_parameter_builder_configs,
            column=f"{DOMAIN_KWARGS_PARAMETER_FULLY_QUALIFIED_NAME}{FULLY_QUALIFIED_PARAMETER_NAME_SEPARATOR_CHARACTER}column",
            min_value=f"{column_standard_deviation_values_range_parameter_builder_for_validations.fully_qualified_parameter_name}{FULLY_QUALIFIED_PARAMETER_NAME_SEPARATOR_CHARACTER}{FULLY_QUALIFIED_PARAMETER_NAME_VALUE_KEY}[0]",
            max_value=f"{column_standard_deviation_values_range_parameter_builder_for_validations.fully_qualified_parameter_name}{FULLY_QUALIFIED_PARAMETER_NAME_SEPARATOR_CHARACTER}{FULLY_QUALIFIED_PARAMETER_NAME_VALUE_KEY}[1]",
            strict_min=f"{VARIABLES_KEY}strict_min",
            strict_max=f"{VARIABLES_KEY}strict_max",
            meta={
                "profiler_details": f"{column_standard_deviation_values_range_parameter_builder_for_validations.fully_qualified_parameter_name}{FULLY_QUALIFIED_PARAMETER_NAME_SEPARATOR_CHARACTER}{FULLY_QUALIFIED_PARAMETER_NAME_METADATA_KEY}",
            },
        )

        # Step-5: Instantiate and return "Rule" object, comprised of "variables", "domain_builder", "parameter_builders", and "expectation_configuration_builders" components.

        variables: dict = {
            "mostly": 1.0,
            "strict_min": False,
            "strict_max": False,
            "quantiles": [
                0.25,
                0.5,
                0.75,
            ],
            "allow_relative_error": "linear",
            "bins": 10,
            "false_positive_rate": 0.05,
            "quantile_statistic_interpolation_method": "auto",
            "estimator": "bootstrap",
            "n_resamples": 9999,
            "random_seed": None,
            "include_estimator_samples_histogram_in_details": False,
            "truncate_values": {
                "lower_bound": None,
                "upper_bound": None,
            },
            "round_decimals": 1,
        }
        parameter_builders: List[ParameterBuilder] = [
            column_histogram_metric_multi_batch_parameter_builder_for_metrics,
            column_column_quantile_values_metric_multi_batch_parameter_builder_for_metrics,
            column_min_metric_multi_batch_parameter_builder_for_metrics,
            column_max_metric_multi_batch_parameter_builder_for_metrics,
            column_median_metric_multi_batch_parameter_builder_for_metrics,
            column_mean_metric_multi_batch_parameter_builder_for_metrics,
            column_standard_deviation_metric_multi_batch_parameter_builder_for_metrics,
        ]
        expectation_configuration_builders: List[ExpectationConfigurationBuilder] = [
            expect_column_min_to_be_between_expectation_configuration_builder,
            expect_column_max_to_be_between_expectation_configuration_builder,
            expect_column_values_to_be_between_expectation_configuration_builder,
            expect_expect_column_quantile_values_to_be_between_expectation_configuration_builder,
            expect_column_median_to_be_between_expectation_configuration_builder,
            expect_column_mean_to_be_between_expectation_configuration_builder,
            expect_column_standard_deviation_to_be_between_expectation_configuration_builder,
        ]
        rule: Rule = Rule(
            name="numeric_columns_rule",
            variables=variables,
            domain_builder=numeric_column_type_domain_builder,
            parameter_builders=parameter_builders,
            expectation_configuration_builders=expectation_configuration_builders,
        )

        return rule

    @staticmethod
    def _build_datetime_columns_rule() -> Rule:
        """
        This method builds "Rule" object focused on emitting "ExpectationConfiguration" objects for datetime columns.
        """

        # Step-1: Instantiate "ColumnDomainBuilder" for selecting proper datetime columns (not "datetime-looking" text).

        datetime_column_type_domain_builder: ColumnDomainBuilder = ColumnDomainBuilder(
            include_column_names=None,
            exclude_column_names=None,
            include_column_name_suffixes=None,
            exclude_column_name_suffixes=None,
            semantic_type_filter_module_name=None,
            semantic_type_filter_class_name=None,
            include_semantic_types=[
                SemanticDomainTypes.DATETIME,
            ],
            exclude_semantic_types=[
                SemanticDomainTypes.TEXT,
            ],
            data_context=None,
        )

        # Step-2: Declare "ParameterBuilder" for every metric of interest.

        column_histogram_metric_multi_batch_parameter_builder_for_metrics: ParameterBuilder = DataAssistant.commonly_used_parameter_builders.get_column_histogram_metric_multi_batch_parameter_builder(
            json_serialize=True
        )
        column_column_quantile_values_metric_multi_batch_parameter_builder_for_metrics: ParameterBuilder = DataAssistant.commonly_used_parameter_builders.get_column_quantile_values_metric_multi_batch_parameter_builder(
            json_serialize=True
        )
        column_min_metric_multi_batch_parameter_builder_for_metrics: ParameterBuilder = DataAssistant.commonly_used_parameter_builders.get_column_min_metric_multi_batch_parameter_builder(
            json_serialize=True
        )
        column_max_metric_multi_batch_parameter_builder_for_metrics: ParameterBuilder = DataAssistant.commonly_used_parameter_builders.get_column_max_metric_multi_batch_parameter_builder(
            json_serialize=True
        )
        column_median_metric_multi_batch_parameter_builder_for_metrics: ParameterBuilder = DataAssistant.commonly_used_parameter_builders.get_column_median_metric_multi_batch_parameter_builder(
            json_serialize=True
        )
        column_mean_metric_multi_batch_parameter_builder_for_metrics: ParameterBuilder = DataAssistant.commonly_used_parameter_builders.get_column_mean_metric_multi_batch_parameter_builder(
            json_serialize=True
        )
        column_standard_deviation_metric_multi_batch_parameter_builder_for_metrics: ParameterBuilder = DataAssistant.commonly_used_parameter_builders.get_column_standard_deviation_metric_multi_batch_parameter_builder(
            json_serialize=True
        )

        # Step-3: Declare "ParameterBuilder" for every "validation" need in "ExpectationConfigurationBuilder" objects.

        column_min_values_range_parameter_builder_for_validations: ParameterBuilder = DataAssistant.commonly_used_parameter_builders.build_numeric_metric_range_multi_batch_parameter_builder(
            metric_name="column.min",
            metric_value_kwargs=None,
            json_serialize=True,
        )
        column_max_values_range_parameter_builder_for_validations: ParameterBuilder = DataAssistant.commonly_used_parameter_builders.build_numeric_metric_range_multi_batch_parameter_builder(
            metric_name="column.max",
            metric_value_kwargs=None,
            json_serialize=True,
        )

        validation_parameter_builder_configs: Optional[List[ParameterBuilderConfig]]

        # Step-4: Pass "validation" "ParameterBuilderConfig" objects to every "DefaultExpectationConfigurationBuilder", responsible for emitting "ExpectationConfiguration" (with specified "expectation_type").

        validation_parameter_builder_configs = [
            ParameterBuilderConfig(
                **column_min_values_range_parameter_builder_for_validations.to_json_dict(),
            ),
        ]
        expect_column_min_to_be_between_expectation_configuration_builder: DefaultExpectationConfigurationBuilder = DefaultExpectationConfigurationBuilder(
            expectation_type="expect_column_min_to_be_between",
            validation_parameter_builder_configs=validation_parameter_builder_configs,
            column=f"{DOMAIN_KWARGS_PARAMETER_FULLY_QUALIFIED_NAME}{FULLY_QUALIFIED_PARAMETER_NAME_SEPARATOR_CHARACTER}column",
            min_value=f"{column_min_values_range_parameter_builder_for_validations.fully_qualified_parameter_name}{FULLY_QUALIFIED_PARAMETER_NAME_SEPARATOR_CHARACTER}{FULLY_QUALIFIED_PARAMETER_NAME_VALUE_KEY}[0]",
            max_value=f"{column_min_values_range_parameter_builder_for_validations.fully_qualified_parameter_name}{FULLY_QUALIFIED_PARAMETER_NAME_SEPARATOR_CHARACTER}{FULLY_QUALIFIED_PARAMETER_NAME_VALUE_KEY}[1]",
            strict_min=f"{VARIABLES_KEY}strict_min",
            strict_max=f"{VARIABLES_KEY}strict_max",
            meta={
                "profiler_details": f"{column_min_values_range_parameter_builder_for_validations.fully_qualified_parameter_name}{FULLY_QUALIFIED_PARAMETER_NAME_SEPARATOR_CHARACTER}{FULLY_QUALIFIED_PARAMETER_NAME_METADATA_KEY}",
            },
        )

        validation_parameter_builder_configs = [
            ParameterBuilderConfig(
                **column_max_values_range_parameter_builder_for_validations.to_json_dict(),
            ),
        ]
        expect_column_max_to_be_between_expectation_configuration_builder: DefaultExpectationConfigurationBuilder = DefaultExpectationConfigurationBuilder(
            expectation_type="expect_column_max_to_be_between",
            validation_parameter_builder_configs=validation_parameter_builder_configs,
            column=f"{DOMAIN_KWARGS_PARAMETER_FULLY_QUALIFIED_NAME}{FULLY_QUALIFIED_PARAMETER_NAME_SEPARATOR_CHARACTER}column",
            min_value=f"{column_max_values_range_parameter_builder_for_validations.fully_qualified_parameter_name}{FULLY_QUALIFIED_PARAMETER_NAME_SEPARATOR_CHARACTER}{FULLY_QUALIFIED_PARAMETER_NAME_VALUE_KEY}[0]",
            max_value=f"{column_max_values_range_parameter_builder_for_validations.fully_qualified_parameter_name}{FULLY_QUALIFIED_PARAMETER_NAME_SEPARATOR_CHARACTER}{FULLY_QUALIFIED_PARAMETER_NAME_VALUE_KEY}[1]",
            strict_min=f"{VARIABLES_KEY}strict_min",
            strict_max=f"{VARIABLES_KEY}strict_max",
            meta={
                "profiler_details": f"{column_max_values_range_parameter_builder_for_validations.fully_qualified_parameter_name}{FULLY_QUALIFIED_PARAMETER_NAME_SEPARATOR_CHARACTER}{FULLY_QUALIFIED_PARAMETER_NAME_METADATA_KEY}",
            },
        )

        validation_parameter_builder_configs = [
            ParameterBuilderConfig(
                **column_min_values_range_parameter_builder_for_validations.to_json_dict(),
            ),
            ParameterBuilderConfig(
                **column_max_values_range_parameter_builder_for_validations.to_json_dict(),
            ),
        ]
        expect_column_values_to_be_between_expectation_configuration_builder: DefaultExpectationConfigurationBuilder = DefaultExpectationConfigurationBuilder(
            expectation_type="expect_column_values_to_be_between",
            validation_parameter_builder_configs=validation_parameter_builder_configs,
            column=f"{DOMAIN_KWARGS_PARAMETER_FULLY_QUALIFIED_NAME}{FULLY_QUALIFIED_PARAMETER_NAME_SEPARATOR_CHARACTER}column",
            min_value=f"{column_min_values_range_parameter_builder_for_validations.fully_qualified_parameter_name}{FULLY_QUALIFIED_PARAMETER_NAME_SEPARATOR_CHARACTER}{FULLY_QUALIFIED_PARAMETER_NAME_VALUE_KEY}[0]",
            max_value=f"{column_max_values_range_parameter_builder_for_validations.fully_qualified_parameter_name}{FULLY_QUALIFIED_PARAMETER_NAME_SEPARATOR_CHARACTER}{FULLY_QUALIFIED_PARAMETER_NAME_VALUE_KEY}[1]",
            mostly=f"{VARIABLES_KEY}mostly",
            strict_min=f"{VARIABLES_KEY}strict_min",
            strict_max=f"{VARIABLES_KEY}strict_max",
            meta={
                "profiler_details": {
                    "column_min_values_range_estimator": f"{column_min_values_range_parameter_builder_for_validations.fully_qualified_parameter_name}{FULLY_QUALIFIED_PARAMETER_NAME_SEPARATOR_CHARACTER}{FULLY_QUALIFIED_PARAMETER_NAME_METADATA_KEY}",
                    "column_max_values_range_estimator": f"{column_max_values_range_parameter_builder_for_validations.fully_qualified_parameter_name}{FULLY_QUALIFIED_PARAMETER_NAME_SEPARATOR_CHARACTER}{FULLY_QUALIFIED_PARAMETER_NAME_METADATA_KEY}",
                },
            },
        )

        # Step-5: Instantiate and return "Rule" object, comprised of "variables", "domain_builder", "parameter_builders", and "expectation_configuration_builders" components.

        variables: dict = {
            "mostly": 1.0,
            "strict_min": False,
            "strict_max": False,
            "bins": 10,
            "false_positive_rate": 0.05,
            "quantile_statistic_interpolation_method": "auto",
            "estimator": "bootstrap",
            "n_resamples": 9999,
            "random_seed": None,
            "include_estimator_samples_histogram_in_details": False,
            "truncate_values": {
                "lower_bound": None,
                "upper_bound": None,
            },
            "round_decimals": 1,
        }
        parameter_builders: List[ParameterBuilder] = [
            column_histogram_metric_multi_batch_parameter_builder_for_metrics,
            column_column_quantile_values_metric_multi_batch_parameter_builder_for_metrics,
            column_min_metric_multi_batch_parameter_builder_for_metrics,
            column_max_metric_multi_batch_parameter_builder_for_metrics,
            column_median_metric_multi_batch_parameter_builder_for_metrics,
            column_mean_metric_multi_batch_parameter_builder_for_metrics,
            column_standard_deviation_metric_multi_batch_parameter_builder_for_metrics,
        ]
        expectation_configuration_builders: List[ExpectationConfigurationBuilder] = [
            expect_column_min_to_be_between_expectation_configuration_builder,
            expect_column_max_to_be_between_expectation_configuration_builder,
            expect_column_values_to_be_between_expectation_configuration_builder,
        ]
        rule: Rule = Rule(
            name="datetime_columns_rule",
            variables=variables,
            domain_builder=datetime_column_type_domain_builder,
            parameter_builders=parameter_builders,
            expectation_configuration_builders=expectation_configuration_builders,
        )

        return rule

    @staticmethod
    def _build_categorical_columns_rule() -> Rule:
        """
        This method builds "Rule" object focused on emitting "ExpectationConfiguration" objects for categorical columns.
        """

        # Step-1: Instantiate "CategoricalColumnDomainBuilder" for selecting columns containing "FEW" discrete values.

        categorical_column_type_domain_builder: CategoricalColumnDomainBuilder = (
            CategoricalColumnDomainBuilder(
                include_column_names=None,
                exclude_column_names=None,
                include_column_name_suffixes=None,
                exclude_column_name_suffixes=None,
                semantic_type_filter_module_name=None,
                semantic_type_filter_class_name=None,
                include_semantic_types=None,
                exclude_semantic_types=None,
                allowed_semantic_types_passthrough=None,
                limit_mode=CardinalityLimitMode.FEW,
                max_unique_values=None,
                max_proportion_unique=None,
                data_context=None,
            )
        )

        # Step-2: Declare "ParameterBuilder" for every metric of interest.

        column_distinct_values_count_metric_multi_batch_parameter_builder_for_metrics: ParameterBuilder = DataAssistant.commonly_used_parameter_builders.get_column_distinct_values_count_metric_multi_batch_parameter_builder(
            json_serialize=True
        )
        metric_name: str = "column.value_counts"
        column_value_counts_metric_multi_batch_parameter_builder_for_metrics: ParameterBuilder = MetricMultiBatchParameterBuilder(
            name=metric_name,
            metric_name=metric_name,
            metric_domain_kwargs=DOMAIN_KWARGS_PARAMETER_FULLY_QUALIFIED_NAME,
            metric_value_kwargs={
                "sort": "value",
            },
            enforce_numeric_metric=False,
            replace_nan_with_zero=False,
            reduce_scalar_metric=True,
            evaluation_parameter_builder_configs=None,
            json_serialize=True,
            data_context=None,
        )

        # Step-3: Declare "ParameterBuilder" for every "validation" need in "ExpectationConfigurationBuilder" objects.

        value_set_multi_batch_parameter_builder_for_validations: ParameterBuilder = (
            ValueSetMultiBatchParameterBuilder(
                name="value_set_estimator",
                metric_domain_kwargs=DOMAIN_KWARGS_PARAMETER_FULLY_QUALIFIED_NAME,
                metric_value_kwargs=None,
                evaluation_parameter_builder_configs=None,
                json_serialize=True,
                data_context=None,
            )
        )
        column_distinct_values_count_range_parameter_builder_for_validations: ParameterBuilder = DataAssistant.commonly_used_parameter_builders.build_numeric_metric_range_multi_batch_parameter_builder(
            metric_name="column.distinct_values.count",
            metric_value_kwargs=None,
            json_serialize=True,
        )
        column_unique_proportion_range_parameter_builder_for_validations: ParameterBuilder = DataAssistant.commonly_used_parameter_builders.build_numeric_metric_range_multi_batch_parameter_builder(
            metric_name="column.unique_proportion",
            metric_value_kwargs=None,
            json_serialize=True,
        )

        validation_parameter_builder_configs: Optional[List[ParameterBuilderConfig]]

        # Step-4: Pass "validation" "ParameterBuilderConfig" objects to every "DefaultExpectationConfigurationBuilder", responsible for emitting "ExpectationConfiguration" (with specified "expectation_type").

        validation_parameter_builder_configs = [
            ParameterBuilderConfig(
                **value_set_multi_batch_parameter_builder_for_validations.to_json_dict(),
            ),
        ]
        expect_column_values_to_be_in_set_expectation_configuration_builder: DefaultExpectationConfigurationBuilder = DefaultExpectationConfigurationBuilder(
            expectation_type="expect_column_values_to_be_in_set",
            validation_parameter_builder_configs=validation_parameter_builder_configs,
            column=f"{DOMAIN_KWARGS_PARAMETER_FULLY_QUALIFIED_NAME}{FULLY_QUALIFIED_PARAMETER_NAME_SEPARATOR_CHARACTER}column",
            value_set=f"{value_set_multi_batch_parameter_builder_for_validations.fully_qualified_parameter_name}{FULLY_QUALIFIED_PARAMETER_NAME_SEPARATOR_CHARACTER}{FULLY_QUALIFIED_PARAMETER_NAME_VALUE_KEY}",
            mostly=f"{VARIABLES_KEY}mostly",
            meta={
                "profiler_details": f"{value_set_multi_batch_parameter_builder_for_validations.fully_qualified_parameter_name}{FULLY_QUALIFIED_PARAMETER_NAME_SEPARATOR_CHARACTER}{FULLY_QUALIFIED_PARAMETER_NAME_METADATA_KEY}",
            },
        )

        validation_parameter_builder_configs = [
            ParameterBuilderConfig(
                **column_distinct_values_count_range_parameter_builder_for_validations.to_json_dict(),
            ),
        ]
        expect_column_unique_value_count_to_be_between_expectation_configuration_builder: DefaultExpectationConfigurationBuilder = DefaultExpectationConfigurationBuilder(
            expectation_type="expect_column_unique_value_count_to_be_between",
            validation_parameter_builder_configs=validation_parameter_builder_configs,
            column=f"{DOMAIN_KWARGS_PARAMETER_FULLY_QUALIFIED_NAME}{FULLY_QUALIFIED_PARAMETER_NAME_SEPARATOR_CHARACTER}column",
            min_value=f"{column_distinct_values_count_range_parameter_builder_for_validations.fully_qualified_parameter_name}{FULLY_QUALIFIED_PARAMETER_NAME_SEPARATOR_CHARACTER}{FULLY_QUALIFIED_PARAMETER_NAME_VALUE_KEY}[0]",
            max_value=f"{column_distinct_values_count_range_parameter_builder_for_validations.fully_qualified_parameter_name}{FULLY_QUALIFIED_PARAMETER_NAME_SEPARATOR_CHARACTER}{FULLY_QUALIFIED_PARAMETER_NAME_VALUE_KEY}[1]",
            strict_min=f"{VARIABLES_KEY}strict_min",
            strict_max=f"{VARIABLES_KEY}strict_max",
            meta={
                "profiler_details": f"{column_distinct_values_count_range_parameter_builder_for_validations.fully_qualified_parameter_name}{FULLY_QUALIFIED_PARAMETER_NAME_SEPARATOR_CHARACTER}{FULLY_QUALIFIED_PARAMETER_NAME_METADATA_KEY}",
            },
        )

        validation_parameter_builder_configs = [
            ParameterBuilderConfig(
                **column_unique_proportion_range_parameter_builder_for_validations.to_json_dict(),
            ),
        ]
        expect_column_proportion_of_unique_values_to_be_between_expectation_configuration_builder: DefaultExpectationConfigurationBuilder = DefaultExpectationConfigurationBuilder(
            expectation_type="expect_column_proportion_of_unique_values_to_be_between",
            validation_parameter_builder_configs=validation_parameter_builder_configs,
            column=f"{DOMAIN_KWARGS_PARAMETER_FULLY_QUALIFIED_NAME}{FULLY_QUALIFIED_PARAMETER_NAME_SEPARATOR_CHARACTER}column",
            min_value=f"{column_unique_proportion_range_parameter_builder_for_validations.fully_qualified_parameter_name}{FULLY_QUALIFIED_PARAMETER_NAME_SEPARATOR_CHARACTER}{FULLY_QUALIFIED_PARAMETER_NAME_VALUE_KEY}[0]",
            max_value=f"{column_unique_proportion_range_parameter_builder_for_validations.fully_qualified_parameter_name}{FULLY_QUALIFIED_PARAMETER_NAME_SEPARATOR_CHARACTER}{FULLY_QUALIFIED_PARAMETER_NAME_VALUE_KEY}[1]",
            strict_min=f"{VARIABLES_KEY}strict_min",
            strict_max=f"{VARIABLES_KEY}strict_max",
            meta={
                "profiler_details": f"{column_unique_proportion_range_parameter_builder_for_validations.fully_qualified_parameter_name}{FULLY_QUALIFIED_PARAMETER_NAME_SEPARATOR_CHARACTER}{FULLY_QUALIFIED_PARAMETER_NAME_METADATA_KEY}",
            },
        )

        # Step-5: Instantiate and return "Rule" object, comprised of "variables", "domain_builder", "parameter_builders", and "expectation_configuration_builders" components.

        variables: dict = {
            "mostly": 1.0,
            "strict_min": False,
            "strict_max": False,
            "false_positive_rate": 0.05,
            "quantile_statistic_interpolation_method": "auto",
            "estimator": "bootstrap",
            "n_resamples": 9999,
            "random_seed": None,
            "include_estimator_samples_histogram_in_details": False,
            "truncate_values": {
                "lower_bound": 0.0,
                "upper_bound": None,
            },
            "round_decimals": 1,
        }
        parameter_builders: List[ParameterBuilder] = [
            column_distinct_values_count_metric_multi_batch_parameter_builder_for_metrics,
            column_value_counts_metric_multi_batch_parameter_builder_for_metrics,
        ]
        expectation_configuration_builders: List[ExpectationConfigurationBuilder] = [
            expect_column_values_to_be_in_set_expectation_configuration_builder,
            expect_column_unique_value_count_to_be_between_expectation_configuration_builder,
            expect_column_proportion_of_unique_values_to_be_between_expectation_configuration_builder,
        ]
        rule: Rule = Rule(
            name="categorical_columns_rule",
            variables=variables,
            domain_builder=categorical_column_type_domain_builder,
            parameter_builders=parameter_builders,
            expectation_configuration_builders=expectation_configuration_builders,
        )

        return rule
