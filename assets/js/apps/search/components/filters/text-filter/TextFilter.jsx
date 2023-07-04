import React, { useState, useEffect } from 'react';
import Form from 'react-bootstrap/Form';
import InputGroup from 'react-bootstrap/InputGroup';
import FormControl from 'react-bootstrap/FormControl';
import Button from 'react-bootstrap/Button';
import PropTypes from 'prop-types';
import FilterError from "../filter-error/FilterError";

const _getValueContent = (value) => {
    if (value) {
        if (value.op === "is") {
            // If this is an exact match filter,
            // the value would be the first array element of content. 
            // This is because an "IS" operator filter
            // uses an array for value.
            return value.content[0];
        } else if (value.op === "contains") {
            // If this is a fuzzy match filter,
            // the value would just be the content string.
            return value.content;
        } else {
            return "";
        }
    } else {
        return "";
    }
}

const TextFilter = ({ value, options, onValueChange }) => {
    // Make a copy of the options first.
    options = Object.assign({}, options);
    if (!options.name) {
        options.name = "Missing filter name";
    }
    if (!options.hint) {
        options.hint = "";
    }
    const initialState = _getValueContent(value);
    const [localValue, setLocalValue] = useState(initialState);
    const [isValidValue, setIsValidValue] = useState(true);
    useEffect(() => {
        // After the filter is initialised, the value may be
        // updated externally - for example, we might restore an old value from
        // query string in shareable URL.
        // We update the local value when it is updated.
        const newValue = _getValueContent(value);
        if (newValue !== localValue) {
            setLocalValue(newValue);
        }
    }, [value])
    const handleValueChange = (e) => {
        validateValue(e.target.value);
        setLocalValue(e.target.value);
    };

    const validateValue = (value) => {
        console.log(value);
        value.length < 1000 ? setIsValidValue(true) : setIsValidValue(false);
    }

    // We should disable the filter button if there's nothing in the filter box.
    // But we should be able to clear a field if there's a value on the filter.
    const canChangeValue = localValue || value;


    const handleSubmit = (e) => {
        e.preventDefault();
        if (!canChangeValue) {
            return;
        }
        if (localValue === "") {
            onValueChange(null);
        } else {
            if (options.isExact) {
                onValueChange({ op: "is", content: [localValue] });
            } else {
                onValueChange({ op: "contains", content: localValue });
            }
        }
    };
    return (
        <Form onSubmit={handleSubmit}>
            <InputGroup>
                <FormControl isInvalid={!isValidValue} onChange={handleValueChange} 
                    value={localValue} aria-label="Filter input" 
                    placeholder={options.hint}
                ></FormControl>
                <InputGroup.Append>
                    <Button type="submit" aria-label="Filter results" variant={canChangeValue ? "secondary" : "outline-secondary"}>Filter</Button>
                </InputGroup.Append>
            </InputGroup>
            {isValidValue ? null :
                <FilterError
                    message={"Character limit exceeded"}
                    longMessage="This text input exceeds the 1000 character limit."
                ></FilterError>
            }
        </Form>
    );
}

TextFilter.propTypes = {
    value: PropTypes.shape({
        content: PropTypes.string.isRequired,
        op: PropTypes.string.isRequired
    }),
    options: PropTypes.object,
    onValueChange: PropTypes.func.isRequired
}

export default TextFilter;