import React, { useMemo } from 'react';
import { useDispatch } from 'react-redux'
import PropTypes from "prop-types";
import Accordion from 'react-bootstrap/Accordion';
import Form from 'react-bootstrap/Form';
import Card from 'react-bootstrap/Card';
import TextFilter from "../text-filter/TextFilter";
import NumberRangeFilter from '../range-filter/NumberRangeFilter';
import DateRangeFilter from '../date-filter/DateRangeFilter';
import { updateFilter, removeFilter } from '../../filterSlice';
import { runSearch } from "../../searchSlice";
import CategoryFilter from '../category-filter/CategoryFilter';
import './TypeSchemaList.css';

// A hook for converting a hashmap of values into a list.
const useAsList = (jsObject = {}) => (
    useMemo(() => (
        Object.keys(jsObject)
                .map(key => jsObject[key]))
    ,[jsObject])
);

const mapTypeToFilter = (type) => {
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
                    const { value, data_type: parameterType, full_name, id: parameterId } = param,
                        ApplicableFilter = mapTypeToFilter(param.data_type);
                    return (
                            <div key={parameterId} className="single-schema-list__filter">
                                <h5 className="single-schema-list__filter-label">{full_name}</h5>
                                <ApplicableFilter 
                                    value={value} 
                                    onValueChange={
                                        onValueChange.bind(
                                            this, 
                                            parameterType, 
                                            schemaId, 
                                            parameterId)
                                    } />
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
    const handleValueChange = (parameterType, schemaId, parameterId, filterValues) => {
        const changedValues = {
            field: {
                kind: "schemaParameter",
                target: [schemaId, parameterId],
                type: parameterType
            },
            value:filterValues
        }
        if (filterValues === null){
            dispatch(removeFilter(changedValues));
        } else {
            dispatch(updateFilter(changedValues));
        }
        dispatch(runSearch());
    };
    return <PureSchemaFilterList {...props} onValueChange={handleValueChange} />

}

const TypeSchemaList = ({ value: schemaValue, options, onValueChange }) => {
    const {allIds : schemasAsList, byId : schemas } = options.schemas || {byId: {}, allIds: []};
    let activeSchemas;
    if (!schemaValue) {
        // If there is no filter on what schemas to show, we show all of them.
        activeSchemas = schemasAsList;
    } else {
        activeSchemas = schemaValue.content;
    }

    const schemaList = useMemo(() => (
        // Return the schema list in format expected by CategoryFilter
        {
            allIds: schemasAsList,
            byId: schemasAsList.reduce((acc,schemaId) => {
                acc[schemaId] = {
                    label: schemas[schemaId].schema_name
                };
                return acc;
            },{})
        }
    ),[schemasAsList, schemas]);


    return (
        <div>
                {
                    schemasAsList.length !== 0 ?
                        <h4 className="type-schema-list__title">Show me</h4> :
                        null
                }

                <CategoryFilter value={schemaValue} onValueChange={onValueChange} options={{
                    checkAllByDefault: true,
                    categories: schemaList
                }} />
            <Accordion>
                {schemasAsList.map((id) => {
                    const schema = schemas[id],
                        name = schema.schema_name;
                    if (!activeSchemas.includes(id)) {
                        // If schema is not selected, don't show filters for the schema.
                        return null;
                    }
                    return (
                        <Card key={name}>
                            <Accordion.Toggle as={Card.Header} eventKey={id}>
                                {name}
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
        schemas: PropTypes.shape({
            allIds: PropTypes.array,
            byId: PropTypes.object
        })
    }),
    onValueChange: PropTypes.func.isRequired
};

export default TypeSchemaList;