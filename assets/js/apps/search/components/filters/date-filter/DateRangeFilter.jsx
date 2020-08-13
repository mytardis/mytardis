import React, { useState, useEffect } from 'react';
import Form from 'react-bootstrap/Form';
import Button from 'react-bootstrap/Button';
import PropTypes from 'prop-types';
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
    const { start, end } = value;
    // A number range filter value is empty if both values are null values.
    return isNone(start) && isNone(end);
};

const toSubmitValue = localValue => {
    // Replace empty string value with null to represent null parameter value.
    if (!localValue) {
        return null;
    }
    const submitValue = [];
    if (!isNone(localValue.start)) {
        if (typeof localValue.start == "object") {
            submitValue.push({
                op: ">=",
                content: localValue.start.toISOString()
            });
        }
    }
    if (!isNone(localValue.end)) {
        if (typeof localValue.end == "object") {
            submitValue.push({
                op: "<=",
                content:localValue.end.toISOString()
            })
        }
    }
    if (submitValue.length == 0) {
        // Return a null to represent no filter value.
        return null;
    }
    return submitValue;
}

const toLocalValue = submitValue => {
    if (!submitValue) {
        return {};
    }
    if (!Array.isArray(submitValue)) {
        submitValue = [submitValue];
    }
    const localValue = {start: null, end: null};
    const startValue = submitValue.filter(value => value.op === ">=");
    const endValue = submitValue.filter(value => value.op === "<=");
    if (startValue.length > 0) {
        localValue.start = moment(startValue[0].content);
    }
    if (endValue.length > 0) {
        localValue.end = moment(endValue[0].content);
    }
    return localValue;
}

const DateRangeFilter = ({ value, options, onValueChange }) => {
    // Make a copy of the options first.
    options = Object.assign({},options);
    if (!options.name) {
        options.name = "missingFilterName";
    }
    if (!options.hintStart) {
        options.hintStart = "MM/DD/YYYY";
    }
    if (!options.hintEnd) {
        options.hintEnd = "MM/DD/YYYY";
    }

    const [localValue, setLocalValue] = useState(toLocalValue(value));

    useEffect(() => {
        // Update the filter when there is a new value,
        // for when the filter value is externally updated
        // e.g. from URL.
        setLocalValue(toLocalValue(value));
    },[value]);

    const handleValueChange = (type, valueFromForm) => {
        // Copy the value object, then assign new value into either "start" or "end".
        const newValue = Object.assign({}, localValue);
        newValue[type] = valueFromForm;
        // React Datetime returns a string if the user enters invalid information.
        if (type === "start" && typeof newValue.start == "object") {
            if (!options.hideEnd && (!newValue.end || newValue.start.isAfter(newValue.end))) {
                // If we are setting start date and there is no end date OR end date is earlier
                //than start date, we auto-fill end date to be same as start date
                newValue.end = newValue.start;
            }
        } else if (type === "end" && typeof newValue.end == "object") {
            if (!options.hideStart && (!newValue.start || newValue.end.isBefore(newValue.start))) {
                // If setting end date and there's no start date OR if new end date is before the start date,
                // we auto-fill start date to be same as end date.
                newValue.start = newValue.end;
            }
        }
        setLocalValue(newValue);
    };

    // We should disable the filter button if there's nothing in the filter box.
    // But we should be able to clear a field if there's a value on the filter.
    const canChangeValue = !isValueEmpty(localValue) || !isNone(value);

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
        if (!canChangeValue) {
            return;
        }
        const value = toSubmitValue(localValue);
        onValueChange(value);
    };

    // Give the input boxes ids so labels can be tied back to the field.
    const startFieldId = "start-"+options.name,
        endFieldId = "end-"+options.name;

    return (
        <Form className="date-range-filter" onSubmit={handleSubmit}>
            {options.hideStart ? null :
                <Form.Group className="date-range-filter__field">
                    <Form.Label htmlFor={startFieldId} srOnly={options.hideLabels}>Start</Form.Label>
                    <Datetime
                        value={localValue.start}
                        onChange={handleValueChange.bind(this, "start")}
                        inputProps={{ placeholder: options.hintStart, id: startFieldId }}
                        closeOnSelect={true}
                        dateFormat="L"
                        timeFormat={false}
                    />
                </Form.Group>
            }
            {options.hideEnd ? null : 
                <Form.Group className="date-range-filter__field">
                    <Form.Label htmlFor={endFieldId} srOnly={options.hideLabels}>End</Form.Label>
                    <Datetime
                        value={localValue.end}
                        onChange={handleValueChange.bind(this, "end")}
                        inputProps={{ placeholder: options.hintEnd, id: endFieldId }}
                        closeOnSelect={true}
                        dateFormat="L"
                        timeFormat={false}
                    />
                </Form.Group>
            }
            <Button
                type="submit"
                className="date-range-filter__button"
                aria-label="Filter results"
                variant={canChangeValue ? "secondary" : "outline-secondary"}
            >
                Filter
            </Button>
        </Form>
    );
}

DateRangeFilter.propTypes = {
    value: PropTypes.array,
    options: PropTypes.shape({
        name: PropTypes.string.isRequired
    }).isRequired,
    onValueChange: PropTypes.func.isRequired
}

export default DateRangeFilter;