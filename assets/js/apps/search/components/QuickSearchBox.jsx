import React, { useState } from 'react';
import Button from 'react-bootstrap/Button';
import InputGroup from 'react-bootstrap/InputGroup';
import FormControl from 'react-bootstrap/FormControl';
import Form from 'react-bootstrap/Form';
import PropTypes from 'prop-types';
import { useDispatch } from 'react-redux';
import { runSearch, updateSearchTerm } from './searchSlice';
import "./QuickSearchBox.css";

export function PureQuickSearchBox({searchTerm,onChange,onSubmit}) {
    const handleChange = (e) => {
        onChange(e.target.value);
    };

    const handleSubmit = (e) => {
        e.preventDefault();
        onSubmit(searchTerm);
    };

    return (
        <Form onSubmit={handleSubmit}>
            <FormControl className="quick-search-box__input" onChange={handleChange} value={searchTerm} aria-label="Quick find search input" placeholder="Find by title or description"></FormControl>
            <Button type="submit" aria-label="Quick find search button" variant="primary">Search</Button>
        </Form>
    )
}

PureQuickSearchBox.propTypes = {
    searchTerm: PropTypes.string,
    onChange: PropTypes.func.isRequired,
    onSubmit: PropTypes.func.isRequired
}

const QuickSearchBox = () => {
    const [searchTerm, onTermChange] = useState("");
    const dispatch = useDispatch();
    return (
        <PureQuickSearchBox
            searchTerm={searchTerm}
            onChange={onTermChange}
            onSubmit={() => {
                dispatch(updateSearchTerm(searchTerm));
                dispatch(runSearch());
            }}
        />
            
    )
}

export default QuickSearchBox;