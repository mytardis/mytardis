import React, { useState, useEffect } from "react";
import PropTypes from "prop-types";

import Cookies from "js-cookie";
import AdvancedSearchForm from "./AdvancedSearchForm";

function SimpleSearchForm({ showResults, searchText }) {
  const [simpleSearchText, setSimpleSearchText] = useState(searchText);
  const [advanceSearchVisible, setAdvancedSearchVisible] = useState(false);
  const [isLoading, setIsLoading] = useState(false);
  const toggleAdvancedSearch = () => setAdvancedSearchVisible(!advanceSearchVisible);
  const fetchResults = () => {
    // fetch results
    setIsLoading(true);
    fetch(`/api/v1/search_simple-search/?query=${simpleSearchText}`, {
      method: "get",
      headers: {
        "Accept": "application/json", // eslint-disable-line quote-props
        "Content-Type": "application/json",
        "X-CSRFToken": Cookies.get("csrftoken"),
      },
    }).then(response => response.json())
      .then((data) => {
        showResults(data.objects[0]);
        setIsLoading(false);
      });
  };
  const getInstrumentList = () => {
    const tempList = [];
    fetch("/api/v1/instrument/?limit=0")
      .then(resp => resp.json())
      .then((json) => {
        json.objects.forEach(
          (value) => {
            tempList.push(value.name);
          },
        );
      });
    return (tempList);
  };
  const [instrumentList] = useState(getInstrumentList());
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
  }, searchText);
  return (
    <main>
      <form onSubmit={handleSimpleSearchSubmit} id="simple-search">
        <input
          type="text"
          name="simple_search_text"
          onChange={event => handleSimpleSearchTextChange(event, event.target.value)}
          value={simpleSearchText}
          className="form-control"
          placeholder="Search for Experiments, Datasets, Datafiles"
        />
      </form>
      {isLoading
       && (
       <div className="col-md-12" style={{ textAlign: "center", position: "absolute" }}>
         <div id="spinner" style={{ textAlign: "center" }}>
           <i id="mo-spin-icon" className="fa fa-spinner fa-pulse fa-2x" />
         </div>
       </div>
       )
      }
      <button
        type="button"
        onClick={toggleAdvancedSearch}
        className="btn btn-default dropdown-toggle"
        data-toggle="dropdown"
        aria-expanded="false"
      >
        <span className="caret" />
      </button>
      {
        advanceSearchVisible ? (
          <AdvancedSearchForm
            searchText={simpleSearchText}
            showResults={showResults}
            instrumentList={instrumentList}
          />
        ) : (
          <button
            type="submit"
            className="simple-search btn btn-primary"
            onClick={handleSimpleSearchSubmit}
          >
            <span className="glyphicon glyphicon-search" aria-hidden="true" />
          </button>
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
