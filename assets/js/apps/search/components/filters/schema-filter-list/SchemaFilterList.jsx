import React, { useState, useMemo } from 'react'
import PropTypes from "prop-types";
import Accordion from 'react-bootstrap/Accordion';
import Form from 'react-bootstrap/Form';
import Card from 'react-bootstrap/Card';
import TextFilter from "../text-filter/TextFilter";
import './SchemaFilterList.css';

// A hook for converting a hashmap of values into a list.
const useAsList = (jsObject = {}) => (
    useMemo(() => (
        Object.keys(jsObject)
              .map(key => jsObject[key]))
    ,[jsObject])
);

const handleParameterChange = (schemaId,parameterId) => (value) => {
    console.log(schemaId,parameterId,value);
}

const SingleSchemaFilterList = ({schema}) => {
    const parameters  = schema.parameters,
          schemaId = schema.id,
          paramsAsList = useAsList(parameters);
    return (<>
        {paramsAsList.map(
                param => {
                    const { value, full_name } = param,
                          parameterId = param.id;
                    let ApplicableFilter;
                    switch (param.data_type) {
                        case "STRING":
                            ApplicableFilter = TextFilter;
                        default:
                            console.log("Filter not yet implemented");
                            break;
                    }
                    return (
                            <div className="single-schema-list__filter">
                                <h5 className="single-schema-list__filter-label">{full_name}</h5>
                                <ApplicableFilter value={value} onValueChange={handleParameterChange(schemaId, parameterId)} />
                                <hr />
                            </div>
                    );
                }
        )}
    </>);
    
    
    /*
    const filtersComponents = filters.map((filter) => {
        switch (filter.data_type) {
            case "STRING":
                return (<TextFilter value={})
        }
    })
    return (
        <div>
            {}
        </div>
    )
    */
}

const SchemaFilterList = ({ value, options, onValueChange }) => {
    // Generate a list of schemas based on the objects
    const schemasAsList = useAsList(options.schemas);
    const handleSchemaToggle = (schemaId,e) => {
        if (value.includes(schemaId)) {
            if (value.length == 1) {
                // Prevent switching off all schemas.
                return;
            }
            const newValue = value.filter(schema => schema !== schemaId);
            onValueChange(newValue);
        } else {
            const newValue = value.concat(schemaId);
            onValueChange(newValue);
        }
    }

    const getCheckValue = (id) => {
        return value.includes(id);
    }
    
    return (
        <div>
            <Form.Group>
                <Form.Label>Show me</Form.Label>
                {
                    
                    schemasAsList.map(
                        ({schema_name,id}) => (
                            <Form.Check 
                                key={id}
                                id={"schemaCheck-"+id}
                                type="checkbox" 
                                label={schema_name} 
                                checked={getCheckValue(id)} 
                                onChange={handleSchemaToggle.bind(this,id)} 
                            />
                        )
                    )
                }
            </Form.Group>
            <Accordion>
                {schemasAsList.map((schema) => {
                    const { id, schema_name } = schema;
                    if (!value.includes(id)) {
                        // If schema is not selected, don't show filters for the schema.
                        return null;
                    }
                    return (
                        <Card key={schema_name}>
                            <Accordion.Toggle as={Card.Header} eventKey={schema_name}>
                                {schema_name}
                            </Accordion.Toggle>
                            <Accordion.Collapse eventKey={schema_name}>
                                <Card.Body>
                                    <SingleSchemaFilterList schema={schema} />
                                </Card.Body>
                            </Accordion.Collapse>
                        </Card>
                    );
                })}
            </Accordion>
        </div>
    );
};

SchemaFilterList.propTypes = {
    value: PropTypes.arrayOf(PropTypes.string).isRequired,
    options: PropTypes.shape({
        schemas: PropTypes.object
    }),
    onValueChange: PropTypes.func.isRequired
};

export default SchemaFilterList;