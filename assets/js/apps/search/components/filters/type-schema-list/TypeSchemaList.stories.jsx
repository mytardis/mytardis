import React from 'react'
import TypeSchemaList from './TypeSchemaList';
import { action } from '@storybook/addon-actions';
import makeMockStore from "../../../util/makeMockStore";
import { Provider } from "react-redux";

export default {
  component: TypeSchemaList,
  title: 'Type schema list',
  decorators: [story => <div style={{ padding: '3rem', width:'400px' }}>{story()}</div>],
  excludeStories: /.*Data$/,
};

const mockStore = makeMockStore();

export const schemaData = {
    value: [
      "1",
      "2"
    ],
    onValueChange: action('active schema changed'),
    options: {
      schemas: {
        "1":{
            "parameters": {
              "14":{
                "id":"14",
                "data_type": "STRING",
                "name":"param1",
                "full_name": "Parameter 1"
              },
              "21":{
                "id":"21",
                "data_type": "STRING",
                "name":"param2",
                "full_name": "Parameter 2"
              },
              "25":{
                "id":"25",
                "data_type": "STRING",
                "name":"sensitive_param",
                "full_name": "Sensitive Parameter"
              }
          },
            "schema_name": "Raw data",
            "id":"1",
            "type":"datafiles"
          },
        "2":{
            "parameters": {
              "31":{
                "id":"31",
                "data_type": "STRING",
                "name":"param1",
                "full_name": "Another parameter 1"
              },
              "8":{
                "id":"8",
                "data_type": "STRING",
                "name":"param2",
                "full_name": "Another parameter 2"
              },
              "38":{
                "id":"38",
                "data_type": "STRING",
                "name":"sensitive_param",
                "full_name": "Sensitive Parameter"
              }
            },
            "schema_name": "Biopipeline Output",
            "id":"2",
            "type":"datafiles"
        }
      }
    }
}

export const onlyOneSchemaSelectedData = Object.assign({},schemaData,{
  value: ["1"]
});

export const Default = () => (
  <Provider store={mockStore}>
    <TypeSchemaList {...schemaData} />
  </Provider>
);

export const OnlyOneSelected = () => (
  <Provider store={mockStore}>
    <TypeSchemaList {...onlyOneSchemaSelectedData} />
  </Provider>
);