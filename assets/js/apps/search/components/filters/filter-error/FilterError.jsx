import React, { useRef } from 'react';
import { FiAlertCircle } from 'react-icons/fi';
import { OverlayTrigger, Tooltip } from 'react-bootstrap';
import './FilterError.css';

const FilterError = ({ message, longMessage, showIcon }) => {
    const target = useRef(null);
    return (
        <>
            <OverlayTrigger
                overlay={
                    <Tooltip aria-label="tooltip container" className='filter-error___tooltip'>{longMessage ? longMessage : message}</Tooltip>
                }
                delay={{ show: 250, hide: 400 }}
                placement="bottom"
            >
                <div
                    ref={target}
                    className="filter-error"
                >
                    <p aria-label="Filter error message"
                        className='filter-error___text'>
                        {message}
                    </p>
                    {showIcon ?
                        <FiAlertCircle className="filter-error___icon" aria-label="error message icon"></FiAlertCircle>
                        :
                        null
                    }
                </div>
            </OverlayTrigger>
        </>
    )
}

FilterError.defaultProps = {
    message: 'Invalid input',
    longMessage: null,
    showIcon: false
}

export default FilterError;