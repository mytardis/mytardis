import React, { useState } from 'react';
import Form from 'react-bootstrap/Form';
import InputGroup from 'react-bootstrap/InputGroup';
import FormControl from 'react-bootstrap/FormControl';
import Button from 'react-bootstrap/Button';
import PropTypes from 'prop-types';

const TextFilter = ({value,options,onValueChange}) => {
    if (!options) {
        options = {};
    } 
    if (!options.name){
        options.name = "Missing filter name";
    }
    if (!options.hint) {
        options.hint = "";
    }
    const [localValue, setLocalValue] = useState(value);
    const handleValueChange = (e) => {
        setLocalValue(e.target.value);
    };

    // We should disable the filter button if there's nothing in the filter box.
    // But we should be able to clear a field if there's a value on the filter.
    const canChangeValue =  localValue || value;


    const handleSubmit = (e) => {
        e.preventDefault();
        if (localValue === "") {
            onValueChange(null);
        } else {
            onValueChange({op:"contains",content:localValue});
        }
    };
    return (
        <Form onSubmit={handleSubmit}>
            <InputGroup>
                <FormControl onChange={handleValueChange} value={localValue} aria-label="Filter input" placeholder={options.hint}></FormControl>
                <InputGroup.Append>
                    <Button type="submit" aria-label="Filter results" variant={canChangeValue ? "secondary" :"outline-secondary"} disabled={!canChangeValue}>Filter</Button>
                </InputGroup.Append>
            </InputGroup>
        </Form>
    );
}

TextFilter.propTypes = {
    value: PropTypes.string,
    options: PropTypes.object,
    onValueChange: PropTypes.func.isRequired
}

export default TextFilter;