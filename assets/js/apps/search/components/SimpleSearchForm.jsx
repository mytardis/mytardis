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
    <main>
      <div className="row">
        <div className="mx-auto align-items-center">
          <div className="card align-items-center">
            <div className="card-body">
              <div className="row align-items-center">
                <div className="col-md-12">
                  <form className="form-horizontal" onSubmit={handleSimpleSearchSubmit} id="simple-search">
                    <div className="input-group mb-3">
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
                          className="input-group-text"
                          onClick={handleSimpleSearchSubmit}
                        >
                          <span className="fa fa-search" />
                        </button>
                      </div>
                    </div>
                    <AdvancedSearchForm
                      searchText={simpleSearchText}
                      showResults={showResults}
                    />
                  </form>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
      {isLoading
       && (
       <div className="col-md-12" style={{ textAlign: 'center', position: 'absolute' }}>
         <div id="spinner" style={{ textAlign: 'center' }}>
           <i id="mo-spin-icon" className="fa fa-spinner fa-pulse fa-2x" />
         </div>
       </div>
       )
      }
    </main>
  );
}
SimpleSearchForm.propTypes = {
  showResults: PropTypes.func.isRequired,
  searchText: PropTypes.string.isRequired,
};

export default SimpleSearchForm;
