import React, { useState, useContext} from 'react';
import Button from 'react-bootstrap/Button';
import InputGroup from 'react-bootstrap/InputGroup';
import FormControl from 'react-bootstrap/FormControl';
import Form from 'react-bootstrap/Form';
import PropTypes from 'prop-types';
import SearchInfoContext from './SearchInfoContext';

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
        <InputGroup>
            <FormControl onChange={handleChange} value={searchTerm} aria-label="Quick find search input" placeholder="Find by title or description"></FormControl>
            <InputGroup.Append>
                <Button type="submit" aria-label="Quick find search button" variant={searchTerm ? "secondary" :"outline-secondary"} disabled={!searchTerm}>Search</Button>
            </InputGroup.Append>
        </InputGroup>
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
    const searchInfo = useContext(SearchInfoContext);
    return (
        <PureQuickSearchBox
            searchTerm={searchTerm}
            onChange={onTermChange}
            onSubmit={searchInfo.updateSearch.bind(searchTerm)}
        />
            
    )
}

export default QuickSearchBox;