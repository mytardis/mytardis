import React, { useMemo } from 'react';
import { useDispatch } from 'react-redux'
import PropTypes from "prop-types";
import Accordion from 'react-bootstrap/Accordion';
import Form from 'react-bootstrap/Form';
import Card from 'react-bootstrap/Card';
import TextFilter from "../text-filter/TextFilter";
import NumberRangeFilter from '../range-filter/NumberRangeFilter';
import DateRangeFilter from '../date-filter/DateRangeFilter';
import { updateFilter } from '../../filterSlice';
import './TypeSchemaList.css';

// A hook for converting a hashmap of values into a list.
const useAsList = (jsObject = {}) => (
    useMemo(() => (
        Object.keys(jsObject)
               .map(key => jsObject[key]))
    ,[jsObject])
);

const mapTypeToFilter = (type) => {
    // TODO handle specific fields with particular filters.
    switch (type) {
        case "STRING":
            return TextFilter;
        case "NUMERIC":
            return NumberRangeFilter;
        case "DATETIME":
            return DateRangeFilter;
        default:
            return TextFilter;
    }
}

const PureSchemaFilterList = ({value: schema, onValueChange}) => {
    const { id: schemaId, type: schemaType, parameters } = schema,
            paramsAsList = useAsList(parameters);

    return (<>
        {paramsAsList.map(
                param => {
                    const { value, full_name, id: parameterId } = param,
                          ApplicableFilter = mapTypeToFilter(param.data_type);
                    return (
                            <div key={parameterId} className="single-schema-list__filter">
                                <h5 className="single-schema-list__filter-label">{full_name}</h5>
                                <ApplicableFilter value={value} onValueChange={onValueChange.bind(this, schemaType, schemaId, parameterId)} />
                                <hr />
                            </div>
                    );
                }
        )}
    </>);
    
}

PureSchemaFilterList.propTypes = {
    value: PropTypes.object.isRequired,
    onValueChange: PropTypes.func.isRequired
}   

const SchemaFilterList = (props) => {
    const dispatch = useDispatch();
    const handleValueChange = (schemaType, schemaId, parameterId, filterValues) => {
        if (!Array.isArray(filterValues)){
            filterValues = [filterValues];
        }
        const changedValues = filterValues.map((value) => (
            Object.assign(value,{
                kind: "schemaParameter",
                target: [schemaId, parameterId]
            })
        ));
        dispatch(updateFilter(changedValues));
    };
    return <PureSchemaFilterList {...props} onValueChange={handleValueChange} />
    // const handleValueChange = (schemaId,parameterId,)

}

const TypeSchemaList = ({ value: filterValue, options, onValueChange }) => {
    // Generate a list of schemas based on the objects
    const schemas = options.schemas || {};
    const schemasAsList = useAsList(schemas);
    const toLocalValue = (filterValue) => {
        if (!filterValue || typeof filterValue !== "object" || !Array.isArray(filterValue.content)) {
            // If there is no filter, it means there is no filter
            // on which schemas to show, which means we need to show
            // all schemas.
            return schemasAsList.map((schema) => schema.id);
        }
        const schemas = filterValue.content;
        if (!Array.isArray(schemas)) {
            return [];
        }
        return schemas;
    }
    
    const toSubmitValue = (localValue) => {
        if (localValue.length === schemasAsList.length) {
            // If the local value has as many values as the schema,
            // that means we need to show all schemas, i.e. no filter.
            return null;
        }
        return {
            content: localValue,
            op: "is"
        }
    }

    const activeSchemas = toLocalValue(filterValue);

    const handleSchemaToggle = (schemaId,e) => {
        if (activeSchemas.includes(schemaId)) {
            if (activeSchemas.length == 1) {
                // Prevent switching off all schemas.
                return;
            }
            const newValue = activeSchemas.filter(schema => schema !== schemaId);
            onValueChange(toSubmitValue(newValue));
        } else {
            const newValue = activeSchemas.concat(schemaId);
            onValueChange(toSubmitValue(newValue));
        }
    }

    const getCheckValue = (id) => {
        return activeSchemas.includes(id);
    }
    
    return (
        <div>
            <Form.Group>
                {
                    schemasAsList.length !== 0 ?
                        <Form.Label>Show me</Form.Label> :
                        null
                }
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
                    if (!activeSchemas.includes(id)) {
                        // If schema is not selected, don't show filters for the schema.
                        return null;
                    }
                    return (
                        <Card key={schema_name}>
                            <Accordion.Toggle as={Card.Header} eventKey={id}>
                                {schema_name}
                            </Accordion.Toggle>
                            <Accordion.Collapse eventKey={id}>
                                <Card.Body>
                                    <SchemaFilterList value={schema} />
                                </Card.Body>
                            </Accordion.Collapse>
                        </Card>
                    );
                })}
            </Accordion>
        </div>
    );
};

TypeSchemaList.propTypes = {
    value: PropTypes.object,
    options: PropTypes.shape({
        schemas: PropTypes.object
    }),
    onValueChange: PropTypes.func.isRequired
};

export default TypeSchemaList;