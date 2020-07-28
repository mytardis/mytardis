import React, { useState, useCallback } from 'react'
import PropTypes from 'prop-types';
import Form from "react-bootstrap/Form";

const makeIsFilterValue = (content) => ({op:"is",content});

const CategoryFilter = ({value, onValueChange, options}) => {
    const { categories, checkAllByDefault = false } = options;

    const isChecked = useCallback((id) => {
        if (!value) {
            // If there is no filter, it means there is no filter
            // on which values to show.
            // So whether we show it as checked depends on whether
            // we want to check all values by default.
            return checkAllByDefault;
        }
        // Otherwise, check if ID is one of the filter vlaues.
        return value.content.some(val => val === id);
    },[value, checkAllByDefault]);

    const handleChecked = useCallback((id) => {
        let currValue = value, newValue;
        if (!currValue) {
            currValue = makeIsFilterValue([]);
        }
        if (currValue.content.length === 0 && checkAllByDefault){
            // When checkAllByDefault is enabled and there is
            // no current value, the user sees all of the options
            // as checked, so the expected behaviour should be to
            // uncheck the selected option, while keeping the others
            // checekd.
            newValue = makeIsFilterValue(categories.allIds.filter(arrayId => arrayId !== id));

        } else if (currValue.content.some(val => val === id)) {
            // If the option is already checked, we remove it from value.
            if (currValue.content.length == 1 && checkAllByDefault) {
                // Prevent switching off all schemas.
                return;
            }
            newValue = makeIsFilterValue(currValue.content.filter(val => val !== id));
        }  else {
            // In other cases, we assume we want to add the option to be selected.
            newValue = makeIsFilterValue(currValue.content.concat(id));

        }
        if (newValue.content.length === 0 || (newValue.content.length === categories.allIds.length && checkAllByDefault)){
            // If all categories are selected, then we remove this filter.
            newValue = null;
        }
        onValueChange(newValue);
    },[value, checkAllByDefault, categories.allIds]);

    return (
        <Form.Group>
            {
                categories.allIds.map(
                    (id) => {
                        // Look up the name from schema hashmap
                        const { label } = categories.byId[id];
                        return <Form.Check 
                            key={id}
                            id={"category-check-"+id+label}
                            type="checkbox"
                            label={label} 
                            checked={isChecked(id)} 
                            onChange={handleChecked.bind(this,id)} 
                        />;
                    }
                )
            }
        </Form.Group>
    )
}

CategoryFilter.propTypes = {
    value: PropTypes.object,
    onValueChange: PropTypes.func.isRequired,
    options: PropTypes.shape({
        categories: PropTypes.shape({
            byId: PropTypes.object.isRequired,
            allIds: PropTypes.array.isRequired
        }),
        checkAllByDefault: PropTypes.bool
    })
};

export default CategoryFilter;