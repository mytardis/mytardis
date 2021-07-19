import React, { useState, useEffect } from 'react';
import 'regenerator-runtime/runtime';
import PropTypes from 'prop-types';

import Cookies from 'js-cookie';
import AdvancedSearchForm from './AdvancedSearchForm';


function SimpleSearchForm({ showResults, searchText }) {
  const [simpleSearchText, setSimpleSearchText] = useState(searchText);
  const [isLoading, setIsLoading] = useState(false);
  const fetchResults = () => {
    // fetch results
    setIsLoading(true);
    fetch(`/api/v1/search_simple-search/?query=${simpleSearchText}`, {
      method: 'get',
      headers: {
        'Accept': 'application/json', // eslint-disable-line quote-props
        'Content-Type': 'application/json',
        'X-CSRFToken': Cookies.get('csrftoken'),
      },
    }).then(response => response.json())
      .then((data) => {
        showResults(data.objects[0]);
        setIsLoading(false);
      });
  };
  const handleSimpleSearchSubmit = (e) => {
    e.preventDefault();
    if (!simpleSearchText) {
      return;
    }
    fetchResults();
  };
  const handleSimpleSearchTextChange = (e, newSearchText) => {
    e.preventDefault();
    setSimpleSearchText(newSearchText);
  };
  useEffect(() => {
    if (!searchText && !simpleSearchText) {
      return;
    }
    fetchResults();
  }, [searchText]);
  return (
    <div>
      <form onSubmit={handleSimpleSearchSubmit} id="simple-search" className="my-3">
        <div className="input-group">
          <input
            type="text"
            name="simple_search_text"
            onChange={event => handleSimpleSearchTextChange(event, event.target.value)}
            value={simpleSearchText}
            className="form-control"
            placeholder="Search for Experiments, Datasets, Datafiles"
          />
          <div className="input-group-append">
            <button
              type="button"
              className="btn btn-primary"
              onClick={handleSimpleSearchSubmit}
            >
              <span className="fa fa-search" />
            </button>
          </div>
        </div>
      </form>
      {isLoading && (
        <div class="d-flex justify-content-center mb-3">
          <div class="spinner-border spinner-border-sm text-primary" role="status">
            <span class="sr-only">Loading...</span>
          </div>
        </div>
      )}
      <AdvancedSearchForm
        searchText={simpleSearchText}
        showResults={showResults}
      />
    </div>
  );
}
SimpleSearchForm.propTypes = {
  showResults: PropTypes.func.isRequired,
  searchText: PropTypes.string.isRequired,
};

export default SimpleSearchForm;
