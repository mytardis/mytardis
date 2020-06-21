import React, { useState } from 'react';
import Form from 'react-bootstrap/Form';
import Button from 'react-bootstrap/Button';
import PropTypes from 'prop-types';
import './NumberRangeFilter.css';

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
    const submitValue = Object.assign({},localValue);
    if (isNone(localValue.min)) {
        submitValue.min = null;
    }
    if (isNone(localValue.max)) {
        submitValue.max = null;
    }
    return submitValue;
}

const toLocalValue = submitValue => {
    // Replace null value with empty string to represent null parameter value.
    if (!submitValue) {
        return {};
    }
    const localValue = Object.assign({},submitValue);
    if (isNone(submitValue.min)) {
        localValue.min = "";
    }
    if (isNone(submitValue.max)) {
        localValue.max = "";
    }
    return localValue;
}

const NumberRangeFilter = ({value,options,onValueChange}) => {
    if (!options) {
        options = {};
    } 
    if (!options.name){
        options.name = "Missing filter name";
    }
    if (!options.hint) {
        options.hint = "";
    }
    const [localValue, setLocalValue] = useState(toLocalValue(value));
 
    const handleValueChange = (type,e) => {
        // Copy the value object, then assign new value into either "min" or "max".
        const valueFromForm = e.target.value;
        const newValue = Object.assign({},localValue);
        newValue[type] = valueFromForm;
        setLocalValue(newValue);
    };

    // We should disable the filter button if there's nothing in the filter box.
    // But we should be able to clear a field if there's a value on the filter.
    const canChangeValue =  !isValueEmpty(localValue) || !isValueEmpty(value);
    console.log(localValue, value, canChangeValue);

    const handleSubmit = (e) => {
        e.preventDefault();
        onValueChange(toSubmitValue(localValue));
    };
    return (
        <Form className="num-range-filter" onSubmit={handleSubmit}>
                <div className="num-range-filter__rangefields">
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
                </div>
            <Button 
                type="submit" 
                className="num-range-filter__button" 
                aria-label="Filter results" 
                variant={canChangeValue ? "secondary" :"outline-secondary"} 
                disabled={!canChangeValue}
            >
                Filter
            </Button>
        </Form>
    );
}

NumberRangeFilter.propTypes = {
    value: PropTypes.shape({
        min: PropTypes.number,
        max: PropTypes.number
    }),
    options: PropTypes.object,
    onValueChange: PropTypes.func.isRequired
}

export default NumberRangeFilter;