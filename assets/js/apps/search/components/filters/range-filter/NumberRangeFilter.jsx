import React, { useState, useEffect } from 'react';
import Form from 'react-bootstrap/Form';
import Button from 'react-bootstrap/Button';
import PropTypes from 'prop-types';

const isNone = (value) => {
    // We need empty string to represent an empty field for text fields
    return value === undefined || value === null || value === "";
}

const isValueEmpty = (value) => {
    if (isNone(value)) {
        return true;
    }
    const {min, max} = value;
    // A number range filter value is empty if both values are null values.
    return isNone(min) && isNone(max);
};

const toSubmitValue = localValue => {
    // Replace empty string value with null to represent null parameter value.
    if (!localValue) {
        return {};
    }
    const submitValue = [];
    if (!isNone(localValue.min)) {
        submitValue.push({op:">=",content:localValue.min})
    } 
    if (!isNone(localValue.max)) {
        submitValue.push({op:"<=",content:localValue.max});
    }
    if (submitValue.length === 0){
        return null;
    }
    return submitValue;
}

const toLocalValue = submitValue => {
    // Replace null value with empty string to represent null parameter value.
    if (!submitValue) {
        return {};
    }
    if (!Array.isArray(submitValue)) {
        // Wrap value in array if not already in array.
        submitValue = [submitValue];
    }
    const localValue = {};
    // Iterate over the filter values to get the min and max values.
    submitValue.forEach(filter => {
        if (!filter || !typeof filter === "object" || isNone(filter.op) || isNone(filter.content)) {
            return;
        }
        if (filter.op === ">=") {
            localValue.min = filter.content;
        }
        if (filter.op === "<=") {
            localValue.max = filter.content;
        }
    });
    return localValue;
}

const NumberRangeFilter = ({value,options,onValueChange}) => {
    // Make a copy of the options first.
    options = Object.assign({},options);
    if (!options.name){
        options.name = "Missing filter name";
    }
    if (!options.hint) {
        options.hint = "";
    }
    const [localValue, setLocalValue] = useState(toLocalValue(value));
    useEffect(() => {
        setLocalValue(toLocalValue(value));
    }, [value]);
    const handleValueChange = (type,e) => {
        // Copy the value object, then assign new value into either "min" or "max".
        const valueFromForm = e.target.value;
        const newValue = Object.assign({},localValue);
        newValue[type] = valueFromForm;
        setLocalValue(newValue);
    };

    // We should disable the filter button if there's nothing in the filter box.
    // But we should be able to clear a field if there's a value on the filter.
    const canChangeValue =  !isValueEmpty(localValue) || !isValueEmpty(toLocalValue(value));

    const handleSubmit = (e) => {
        e.preventDefault();
        if (!canChangeValue) {
            return;
        }
        onValueChange(toSubmitValue(localValue));
    };
    return (
        <Form className="num-range-filter" onSubmit={handleSubmit}>
                    <Form.Group className="num-range-filter__field">
                        <Form.Label>Min</Form.Label>
                        <Form.Control  
                            onChange={handleValueChange.bind(this,"min")} 
                            value={localValue.min} 
                            aria-label="Filter input for min value"
                            placeholder={options.hintMin}
                        >
                        </Form.Control>
                    </Form.Group>
                    <Form.Group className="num-range-filter__field">
                        <Form.Label>Max</Form.Label>
                        <Form.Control 
                            onChange={handleValueChange.bind(this,"max")} 
                            value={localValue.max} 
                            aria-label="Filter input for max value"
                            placeholder={options.hintMax}
                        >
                        </Form.Control>
                    </Form.Group>
            <Button 
                type="submit" 
                className="num-range-filter__button" 
                aria-label="Filter results" 
                variant={canChangeValue ? "secondary" :"outline-secondary"} 
            >
                Filter
            </Button>
        </Form>
    );
}

NumberRangeFilter.propTypes = {
    value: PropTypes.array,
    options: PropTypes.object,
    onValueChange: PropTypes.func.isRequired
}

export default NumberRangeFilter;