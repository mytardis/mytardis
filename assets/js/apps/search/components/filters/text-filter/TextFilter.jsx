import React, { useState, useEffect } from 'react';
import Form from 'react-bootstrap/Form';
import InputGroup from 'react-bootstrap/InputGroup';
import FormControl from 'react-bootstrap/FormControl';
import Button from 'react-bootstrap/Button';
import PropTypes from 'prop-types';

const TextFilter = ({value,options,onValueChange}) => { 
    // Make a copy of the options first.
    options = Object.assign({},options);
    if (!options.name){
        options.name = "Missing filter name";
    }
    if (!options.hint) {
        options.hint = "";
    }
    const initialState = value ? value.content : "";
    const [localValue, setLocalValue] = useState( initialState );
    useEffect(() => {
        setLocalValue(value ? value.content : "");
    },[value])
    const handleValueChange = (e) => {
        setLocalValue(e.target.value);
    };

    // We should disable the filter button if there's nothing in the filter box.
    // But we should be able to clear a field if there's a value on the filter.
    const canChangeValue =  localValue || value;


    const handleSubmit = (e) => {
        e.preventDefault();
        if (!canChangeValue) {
            return;
        }
        if (localValue === "") {
            onValueChange(null);
        } else {
            if (options.isExact) {
                onValueChange({op: "is", content: [localValue]});
            } else {
                onValueChange({op:"contains",content:localValue});
            }
        }
    };
    return (
        <Form onSubmit={handleSubmit}>
            <InputGroup>
                <FormControl onChange={handleValueChange} value={localValue} aria-label="Filter input" placeholder={options.hint}></FormControl>
                <InputGroup.Append>
                    <Button type="submit" aria-label="Filter results" variant={canChangeValue ? "secondary" :"outline-secondary"}>Filter</Button>
                </InputGroup.Append>
            </InputGroup>
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