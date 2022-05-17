---
title: How to configure a Validation Result Store in Amazon S3
---

import Prerequisites from '../../connecting_to_your_data/components/prerequisites.jsx'
import TechnicalTag from '@site/docs/term_tags/_tag.mdx';

By default, <TechnicalTag tag="validation_result" text="Validation Results" /> are stored in JSON format in the ``uncommitted/validations/`` subdirectory of your ``great_expectations/`` folder.  Since Validation Results may include examples of data (which could be sensitive or regulated) they should not be committed to a source control system. This guide will help you configure a new storage location for Validation Results in Amazon S3.

<Prerequisites>

- [Configured a Data Context](../../../tutorials/getting_started/tutorial_setup.md).
- [Configured an Expectations Suite](../../../tutorials/getting_started/tutorial_create_expectations.md).
- [Configured a Checkpoint](../../../tutorials/getting_started/tutorial_validate_data.md).
- [Installed boto3](https://github.com/boto/boto3) in your local environment.
- Identified the S3 bucket and prefix where Validation Results will be stored.

</Prerequisites>

## Steps

### 1. Configure boto3 to connect to the Amazon S3 bucket where Validation results will be stored

Instructions on how to set up [boto3](https://github.com/boto/boto3) with AWS can be found at boto3's [documentation site](https://boto3.amazonaws.com/v1/documentation/api/latest/index.html).

### 2. Identify your Data Context Validation Results Store

As with other <TechnicalTag tag="store" text="Stores" />, you can find your <TechnicalTag tag="validation_result_store" text="Validation Results Store" /> with your <TechnicalTag tag="data_context" text="Data Context" />.  Look for the following section in your <TechnicalTag relative="../../../" tag="data_context" text="Data Context's" /> ``great_expectations.yml`` file:

```yaml
validations_store_name: validations_store

stores:
  validations_store:
      class_name: ValidationsStore
      store_backend:
          class_name: TupleFilesystemStoreBackend
          base_directory: uncommitted/validations/
```
The configuration file tells Great Expectations to look for Validation Results in a Store called ``validations_store``. It also creates a ``ValidationsStore`` called ``validations_store`` that is backed by a Filesystem and will store Validation Results under the ``base_directory`` ``uncommitted/validations`` (the default).

### 3. Update your configuration file to include a new Store for Validation Results on S3

In the example below, the new Store's name is set to ``validations_S3_store``, but it can be any name you like.  We also need to make some changes to the ``store_backend`` settings.  The ``class_name`` will be set to ``TupleS3StoreBackend``, ``bucket`` will be set to the address of your S3 bucket, and ``prefix`` will be set to the folder in your S3 bucket where Validation results will be located.

:::caution
If you are also storing <TechnicalTag tag="expectation" text="Expectations" /> in S3 ([How to configure an Expectation store to use Amazon S3](./how_to_configure_an_expectation_store_in_amazon_s3.md)), or DataDocs in S3 ([How to host and share Data Docs on Amazon S3](../configuring_data_docs/how_to_host_and_share_data_docs_on_amazon_s3.md)), then please ensure that the ``prefix`` values are disjoint and one is not a substring of the other.
:::

```yaml
validations_store_name: validations_S3_store

stores:
  validations_S3_store:
      class_name: ValidationsStore
      store_backend:
          class_name: TupleS3StoreBackend
          bucket: '<your_s3_bucket_name>'
          prefix: '<your_s3_bucket_folder_name>'
```

### 4. Copy existing Validation results to the S3 bucket (This step is optional)

One way to copy Validation Results into Amazon S3 is by using the ``aws s3 sync`` command.  As mentioned earlier, the ``base_directory`` is set to ``uncommitted/validations/`` by default. In the example below, two Validation results, ``Validation1`` and ``Validation2`` are copied to Amazon S3.  Your output should looks something like this:

```bash
aws s3 sync '<base_directory>' s3://'<your_s3_bucket_name>'/'<your_s3_bucket_folder_name>'
upload: uncommitted/validations/val1/val1.json to s3://'<your_s3_bucket_name>'/'<your_s3_bucket_folder_name>'/val1.json
upload: uncommitted/validations/val2/val2.json to s3://'<your_s3_bucket_name>'/'<your_s3_bucket_folder_name>'/val2.json
```

### 5. Confirm that the new Validation Results Store has been added by running ``great_expectations store list``

Notice the output contains two Validation Results Stores: the original ``validations_store`` on the local filesystem and the ``validations_S3_store`` we just configured.  This is ok, since Great Expectations will look for Validation Results on the S3 bucket as long as we set the ``validations_store_name`` variable to ``validations_S3_store``.

```bash
great_expectations store list

- name: validations_store
 class_name: ValidationsStore
 store_backend:
   class_name: TupleFilesystemStoreBackend
   base_directory: uncommitted/validations/

- name: validations_S3_store
 class_name: ValidationsStore
 store_backend:
   class_name: TupleS3StoreBackend
   bucket: '<your_s3_bucket_name>'
   prefix: '<your_s3_bucket_folder_name>'
```

### 6. Confirm that the Validations Results Store has been correctly configured

[Run a Checkpoint](../../../tutorials/getting_started/tutorial_validate_data.md) to store results in the new Validation Results Store on S3 then visualize the results by [re-building Data Docs](../../../terms/data_docs.md).
