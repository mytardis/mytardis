import React, { useState } from 'react';
import Form from 'react-bootstrap/Form';
import Button from 'react-bootstrap/Button';
import PropTypes from 'prop-types';
import './DateRangeFilter.css';
import Datetime from 'react-datetime';
import moment from 'moment';

// React Datetime requires CSS to work.
import 'react-datetime/css/react-datetime.css';

const isNone = (value) => {
    // We need empty string to represent an empty field for text fields
    return value === undefined || value === null || value === "";
}

const isValueEmpty = (value) => {
    if (isNone(value)) {
        return true;
    }
    const {start, end} = value;
    // A number range filter value is empty if both values are null values.
    return isNone(start) && isNone(end);
};

const toSubmitValue = localValue => {
    // Replace empty string value with null to represent null parameter value.
    if (!localValue) {
        return {};
    }
    const submitValue = {};
    if (!isNone(localValue.start)) {
        submitValue.start = localValue.start.toISOString();
    }
    if (!isNone(localValue.end)) {
        submitValue.end = localValue.end.toISOString();
    }
    return submitValue;
}

const toLocalValue = submitValue => {
    // Replace null value with empty string to represent null parameter value.
    if (!submitValue) {
        return {};
    }
    const localValue = {};
    if (isNone(submitValue.start)) {
        localValue.start = null;
    } else {
        localValue.start = moment(submitValue.start);
    }
    if (isNone(submitValue.end)) {
        localValue.end = null;
    } else {
        localValue.end = moment(submitValue.end);
    }
    return localValue;
}

const DateRangeFilter = ({value,options,onValueChange}) => {
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
        // Copy the value object, then assign new value into either "start" or "end".
        const valueFromForm = e;
        const newValue = Object.assign({},localValue);
        newValue[type] = valueFromForm;
        setLocalValue(newValue);
    };

    // We should disable the filter button if there's nothing in the filter box.
    // But we should be able to clear a field if there's a value on the filter.
    const canChangeValue =  !isValueEmpty(localValue) || !isValueEmpty(value);
    console.log(localValue, value, canChangeValue);

    const isValidEndDate = (current) => {
        if (!localValue.start) {
            // If there is no start date, user can set any end date
            return true;
        }
        // If there is a start date, then we check the date is after start date.
        return current.isSameOrAfter(localValue.start);
    }

    const handleSubmit = (e) => {
        e.preventDefault();
        const value = toSubmitValue(localValue);
        onValueChange(value);
    };

    return (
        <Form className="date-range-filter" onSubmit={handleSubmit}>
                <div className="date-range-filter__rangefields">
                    <Form.Group className="date-range-filter__field">
                        <Form.Label>Start date</Form.Label>
                        <Datetime 
                            value={localValue.start}
                            onChange={handleValueChange.bind(this,"start")} 
                            inputProps={{placeholder: options.hintStart}}
                            closeOnSelect={true}
                            dateFormat="L"
                            timeFormat={false}
                        />
                    </Form.Group>
                    <Form.Group className="date-range-filter__field">
                        <Form.Label>End date</Form.Label>
                        <Datetime
                            value={localValue.end} 
                            onChange={handleValueChange.bind(this,"end")} 
                            inputProps={{placeholder: options.hintEnd}} 
                            closeOnSelect={true}
                            dateFormat="L"
                            timeFormat={false}
                            isValidDate={isValidEndDate}
                        />
                    </Form.Group>
                </div>
            <Button 
                type="submit" 
                className="date-range-filter__button" 
                aria-label="Filter results" 
                variant={canChangeValue ? "secondary" :"outline-secondary"} 
                disabled={!canChangeValue}
            >
                Filter
            </Button>
        </Form>
    );
}

DateRangeFilter.propTypes = {
    value: PropTypes.shape({
        start: PropTypes.Object,
        end: PropTypes.Object
    }),
    options: PropTypes.object,
    onValueChange: PropTypes.func.isRequired
}

export default DateRangeFilter;