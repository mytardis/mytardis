import React from 'react'
import PropTypes from "prop-types";
import Accordion from 'react-bootstrap/Accordion';
import Card from 'react-bootstrap/Card';
import TextFilter from "../text-filter/TextFilter";

const FilterList = ({ filters, activeFilters,   }) => {
    const filtersComponents = filters.map((filter) => {
        switch (filter.data_type) {
            case "STRING":
                return (<TextFilter value={})
        }
    })
    return (
        <div>
            {}
        </div>
    )
}

const SchemaFilterList = ({ schemas }) => {

    return (
        <Accordion>
            {schemas.map(({ schema_name, parameters }) => (
                <Card key={schema_name}>
                    <Accordion.Toggle as={Card.Header} eventKey={schema_name}>
                        {schema_name}
                    </Accordion.Toggle>
                    <Accordion.Collapse eventKey={schema_name}>
                        <Card.Body>
                        </Card.Body>
                    </Accordion.Collapse>
                </Card>
            ))}
        </Accordion>
    );
};

SchemaFilterList.propTypes = {
    schemas: PropTypes.array.isRequired
};

export default SchemaFilterList;