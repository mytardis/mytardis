/* global getCookie */
import React, { useState } from "react";
import PropTypes from "prop-types";
import DateTime from "react-datetime";
import { Typeahead } from "react-bootstrap-typeahead";

import "react-bootstrap-typeahead/css/Typeahead.css";
import "react-datetime/css/react-datetime.css";

const csrftoken = getCookie("csrftoken");

function AdvancedSearchForm({ searchText, showResults }) {
  const [instrumentList, setInstrumentList] = useState([]);
  const typeOptions = ["Dataset", "Experiment", "Datafile"];
  const [startDate, setStartDate] = useState("");
  // eslint-disable-next-line no-unused-vars
  const [endDate, setEndDate] = useState("");
  const [isLoading, setIsLoading] = useState(false);
  const [formData, setFormData] = useState(
    { text: searchText, TypeTag: typeOptions },
  );
  const getInstrumentList = () => {
    const tempList = [];
    fetch("/api/v1/instrument/")
      .then(resp => resp.json())
      .then((json) => {
        json.objects.forEach(
          (value) => {
            tempList.push(value.name);
          },
        );
      });
    setInstrumentList(tempList);
  };
  const handleAdvancedSearchFormSubmit = (event) => {
    event.preventDefault();
    if (!searchText) {
      return;
    }
    setIsLoading(true);
    // set form data
    setFormData(data => ({ ...data, text: searchText }));
    fetch("/api/v1/search_advance-search/", {
      method: "post",
      headers: {
        "Accept": "application/json", // eslint-disable-line quote-props
        "Content-Type": "application/json",
        "X-CSRFToken": csrftoken,
      },
      body: JSON.stringify(formData),
    }).then(
      response => response.json(),
    ).then(
      (data) => {
        setIsLoading(false);
        showResults(data);
      },
    );
  };
  const validStartDate = current => current.isBefore(DateTime.moment());
  const handleStartDateChange = (value) => {
    setFormData(data => ({ ...data, StartDate: value.toDate() }));
    setStartDate(value.toDate());
  };
  const handleEndDateChange = (value) => {
    setFormData(data => ({ ...data, EndDate: value.toDate() }));
  };
  const validEndDate = current => current.isBefore(DateTime.moment()) && current.isAfter(startDate);
  const handleInstrumentListChange = (selected) => {
    setFormData(data => ({ ...data, InstrumentList: selected }));
  };
  const handleTypeTagChange = (selected) => {
    setFormData(data => ({ ...data, TypeTag: selected }));
  };

  return (
    <form id="adv-search-form" className="form-horizontal">
      <div className="form-group" id="adv-search">
        <label htmlFor="filter">Filter by Date created</label>
        <div className="form-group row">
          <div className="col-xs-6" style={{ paddingLeft: 0, paddingRight: 15 }}>
            <DateTime
              id="select-start-date"
              inputProps={{ placeholder: "Select start date" }}
              timeFormat={false}
              dateFormat="DD-MM-YYYY"
              isValidDate={validStartDate}
              closeOnSelect
              onChange={handleStartDateChange}
            />
          </div>
          <div className="col-xs-6" style={{ paddingRight: 0 }}>
            <DateTime
              inputProps={{ placeholder: "Select end date" }}
              timeFormat={false}
              dateFormat="DD-MM-YYYY"
              isValidDate={validEndDate}
              closeOnSelect
              value={endDate}
              onChange={handleEndDateChange}
            />
          </div>
        </div>

        <label htmlFor="contain">Search In</label>
        <Typeahead
          multiple
          onChange={(selected) => { handleTypeTagChange(selected); }}
          options={typeOptions}
          placeholder="Search in Experiments, Datasets or Datafiles"
          defaultSelected={typeOptions.slice(0, 3)}
        />
        <label htmlFor="contain">Filter by Instrument</label>
        <Typeahead
          multiple
          onFocus={() => getInstrumentList()}
          onChange={(selected) => { handleInstrumentListChange(selected); }}
          placeholder="Start typing to select instruments"
          options={instrumentList}
        />
        <button
          type="submit"
          className="btn btn-primary"
          onClick={handleAdvancedSearchFormSubmit}
        >
          <span className="glyphicon glyphicon-search" aria-hidden="true" />
        </button>
        {isLoading && (
          <div className="col-md-6" style={{ textAlign: "center", position: "absolute" }}>
            <div id="spinner" style={{ textAlign: "center" }}>
              <i id="mo-spin-icon" className="fa fa-spinner fa-pulse fa-2x" />
            </div>
          </div>
        )
        }
      </div>
    </form>
  );
}
AdvancedSearchForm.propTypes = {
  showResults: PropTypes.func.isRequired,
  searchText: PropTypes.string.isRequired,
};

export default AdvancedSearchForm;
