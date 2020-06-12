import React from 'react'
import SchemaFilterList from './SchemaFilterList';
import { action } from '@storybook/addon-actions';

export default {
  component: SchemaFilterList,
  title: 'Schema filter list',
  decorators: [story => <div style={{ padding: '3rem' }}>{story()}</div>],
  excludeStories: /.*Data$/,
};

export const schemaData = {
    schemas: [
        {
          "parameters": [
            {
              "data_type": "STRING",
              "name":"param1",
              "full_name": "Parameter 1"
            },
            {
              "data_type": "STRING",
              "name":"param2",
              "full_name": "Parameter 2"
            },
            {
              "data_type": "STRING",
              "name":"sensitive_param",
              "full_name": "Sensitive Parameter"
            }
          ],
          "schema_name": "Schema_ACL_dataset"
        }
      ]
}

export const Default = () => (
    <SchemaFilterList {...schemaData} />
)
