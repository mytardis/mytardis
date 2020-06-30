import React from 'react'
import SchemaFilterList from './SchemaFilterList';
import { action } from '@storybook/addon-actions';

export default {
  component: SchemaFilterList,
  title: 'Schema filter list',
  decorators: [story => <div style={{ padding: '3rem', width:'400px' }}>{story()}</div>],
  excludeStories: /.*Data$/,
};

export const schemaData = {
    value: [
      "1",
      "2"
    ],
    onValueChange: action('active schema changed'),
    options: {
      schemas: {
        "1":{
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
            "schema_name": "Raw data",
            "id":"1"
          },
        "2":{
            "parameters": [
              {
                "data_type": "STRING",
                "name":"param1",
                "full_name": "Another parameter 1"
              },
              {
                "data_type": "STRING",
                "name":"param2",
                "full_name": "Another parameter 2"
              },
              {
                "data_type": "STRING",
                "name":"sensitive_param",
                "full_name": "Sensitive Parameter"
              }
            ],
            "schema_name": "Biopipeline Output",
            "id":"2"
        }
      }
    }
}

export const onlyOneSchemaSelectedData = Object.assign({},schemaData,{
  value: ["1"]
});

export const Default = () => (
    <SchemaFilterList {...schemaData} />
);

export const OnlyOneSelected = () => (
  <SchemaFilterList {...onlyOneSchemaSelectedData} />
);