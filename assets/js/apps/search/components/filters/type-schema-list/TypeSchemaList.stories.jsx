import React from 'react'
import { PureTypeSchemaList } from './TypeSchemaList';
import { action } from '@storybook/addon-actions';
import makeMockStore from "../../../util/makeMockStore";
import { Provider } from "react-redux";

const mockStore = makeMockStore();

export default {
  component: PureTypeSchemaList,
  title: 'Filters/Type schema list',
  decorators: [story =>   
    <Provider store={mockStore}>
      <div style={{ padding: '3rem', width:'400px' }}>{story()}</div>
    </Provider>],
  excludeStories: /.*Data$/,
};

export const allSchemaIdsData = ["1","2"];

export const schemaData = {
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
};

const defaultProps = {
    value: {
      op:"is",
      content:["1","2"]
    },
    onValueChange: action('active schema changed'),
    options: {
      schemas: {
        allIds: allSchemaIdsData,
        byId: schemaData
      }
    }
}

const onlyOneSchemaSelectedProps = Object.assign({},defaultProps,{
  value: {
    op:"is",
    content:["1"]
  }
});

const noSchemaSelectedProps = Object.assign({}, defaultProps, {
  value: null
})

const noValueProps = Object.assign({}, defaultProps, {
  value: null,
  options: {
    schemas: null
  }
})

export const Default = () => (
  <PureTypeSchemaList {...defaultProps} />
);

export const OnlyOneSelected = () => (
  <PureTypeSchemaList {...onlyOneSchemaSelectedProps} />
);

export const NoSchemaSelected = () => (
  <PureTypeSchemaList {...noSchemaSelectedProps} />
);

export const NoSchemas = () => (
  <PureTypeSchemaList {...noValueProps} />
)