---
title: How to connect to a BigQuery database
---
import Prerequisites from '../components/prerequisites.jsx'
import WhereToRunCode from '../components/where_to_run_code.md'
import NextSteps from '../components/next_steps.md'
import Congratulations from '../components/congratulations.md'
import DatabaseCredentials from '../components/adding_database_credentials.md'
import Tabs from '@theme/Tabs';
import TabItem from '@theme/TabItem';
import TechnicalTag from '@site/docs/term_tags/_tag.mdx';

This guide will help you connect to data in a BigQuery database.
This will allow you to <TechnicalTag tag="validation" text="Validate" /> and explore your data.

<Prerequisites>

- Have access to data in a BigQuery database
- Followed the [Google Cloud Library guide](https://googleapis.dev/python/google-api-core/latest/auth.html) for authentication

</Prerequisites>

## Steps

### 1. Choose how to run the code in this guide

<WhereToRunCode />

### 2. Install required dependencies

First, install the necessary dependencies for Great Expectations to connect to your BigQuery database by running the following in your terminal:

```console
pip install sqlalchemy-bigquery
```

### 3. Add credentials

<DatabaseCredentials />

For this guide we will use a `connection_string` like this:

```
bigquery://<GCP_PROJECT>/<BIGQUERY_DATASET>
```   

### 4. Instantiate your project's DataContext

Import these necessary packages and modules.

```python file=../../../../tests/integration/docusaurus/connecting_to_your_data/database/bigquery_yaml_example.py#L2-L5
```

Load your DataContext into memory using the `get_context()` method.

```python file=../../../../tests/integration/docusaurus/connecting_to_your_data/database/bigquery_yaml_example.py#L24
```

### 5. Configure your Datasource

<Tabs
  groupId="yaml-or-python"
  defaultValue='yaml'
  values={[
  {label: 'YAML', value:'yaml'},
  {label: 'Python', value:'python'},
  ]}>

<TabItem value="yaml">

Put your connection string in this template:

```python file=../../../../tests/integration/docusaurus/connecting_to_your_data/database/bigquery_yaml_example.py#L28-L42
```

Run this code to test your configuration.

```python file=../../../../tests/integration/docusaurus/connecting_to_your_data/database/bigquery_yaml_example.py#L53
```

</TabItem>

<TabItem value="python">

Put your connection string in this template:

```python file=../../../../tests/integration/docusaurus/connecting_to_your_data/database/bigquery_python_example.py#L24-L41
```

Run this code to test your configuration.

```python file=../../../../tests/integration/docusaurus/connecting_to_your_data/database/bigquery_python_example.py#L49
```

</TabItem>

</Tabs>

You will see your database tables listed as `Available data_asset_names` in the output of `test_yaml_config()`.

Feel free to adjust your configuration and re-run `test_yaml_config` as needed.

### 6. Save the Datasource configuration to your DataContext

Save the configuration into your `DataContext` by using the `add_datasource()` function.

<Tabs
  groupId="yaml-or-python"
  defaultValue='yaml'
  values={[
  {label: 'YAML', value:'yaml'},
  {label: 'Python', value:'python'},
  ]}>

<TabItem value="yaml">

```python file=../../../../tests/integration/docusaurus/connecting_to_your_data/database/bigquery_yaml_example.py#L57
```

</TabItem>

<TabItem value="python">

```python file=../../../../tests/integration/docusaurus/connecting_to_your_data/database/bigquery_python_example.py#L53
```

</TabItem>

</Tabs>

### 7. Test your new Datasource

Verify your new <TechnicalTag tag="datasource" text="Datasource" /> by loading data from it into a <TechnicalTag tag="validator" text="Validator" /> using a `BatchRequest`.

<Tabs
  defaultValue='runtime_batch_request'
  values={[
  {label: 'Using a SQL query', value:'runtime_batch_request'},
  {label: 'Using a table name', value:'batch_request'},
  ]}>

<TabItem value="runtime_batch_request">

Here is an example of loading data by specifying a SQL query.

```python file=../../../../tests/integration/docusaurus/connecting_to_your_data/database/bigquery_yaml_example.py#L62-L76
```

</TabItem>

<TabItem value="batch_request">

Here is an example of loading data by specifying an existing table name.

```python file=../../../../tests/integration/docusaurus/connecting_to_your_data/database/bigquery_python_example.py#L78-L89
```

</TabItem>

</Tabs>

<Congratulations />

## Additional Notes

To view the full scripts used in this page, see them on GitHub:

- [bigquery_yaml_example.py](https://github.com/great-expectations/great_expectations/blob/develop/tests/integration/docusaurus/connecting_to_your_data/database/bigquery_yaml_example.py)
- [bigquery_python_example.py](https://github.com/great-expectations/great_expectations/blob/develop/tests/integration/docusaurus/connecting_to_your_data/database/bigquery_python_example.py)

## Next Steps

<NextSteps />
