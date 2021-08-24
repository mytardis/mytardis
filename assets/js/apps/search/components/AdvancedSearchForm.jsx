import Cookies from 'js-cookie';
import React, { useEffect, useState } from 'react';
import PropTypes from 'prop-types';
import DateTime from 'react-datetime';
import { Typeahead } from 'react-bootstrap-typeahead';
import moment from 'moment';

import 'react-bootstrap-typeahead/css/Typeahead.css';
import 'react-datetime/css/react-datetime.css';


function AdvancedSearchForm({ searchText, showResults }) {
  const [advanceSearchText, setAdvanceSearchText] = useState(searchText);
  const [startDate, setStartDate] = useState('');
  const [endDate, setEndDate] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [selectedInstrumentList, setSelectedInstrumentList] = useState([]);
  const typeOptions = ['Dataset', 'Experiment', 'Datafile'];
  const [selectedTypeTag, setSelectedTypeTag] = useState(typeOptions);
  const [instrumentList, setInstrumentList] = useState([]);
  const getFormData = () => {
    let data = { text: advanceSearchText, TypeTag: selectedTypeTag };
    if (startDate !== '') {
      data = { ...data, StartDate: startDate };
    }
    if (endDate !== '') {
      data = { ...data, EndDate: endDate };
    }
    if (selectedInstrumentList.length > 0) {
      data = { ...data, InstrumentList: selectedInstrumentList };
    }
    return data;
  };
  useEffect(() => {
    setAdvanceSearchText(searchText);
  }, [searchText]);
  useEffect(() => {
    async function fetchInstrumentList() {
      const response = await fetch('/api/v1/instrument/?limit=0');
      return response.json();
    }
    const jsonResponse = fetchInstrumentList();
    const instrumentListTemp = [];
    jsonResponse.then((json) => {
      json.objects.forEach((value) => {
        instrumentListTemp.push(value.name);
      });
      return instrumentListTemp;
    }).then((list) => {
      setInstrumentList(list);
    });
  }, [searchText]);

  const handleAdvancedSearchFormSubmit = (event) => {
    event.preventDefault();
    if (!searchText) {
      return;
    }
    setIsLoading(true);
    const formData = getFormData();
    fetch('/api/v1/search_advance-search/', {
      method: 'post',
      headers: {
        'Accept': 'application/json', // eslint-disable-line quote-props
        'Content-Type': 'application/json',
        'X-CSRFToken': Cookies.get('csrftoken'),
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
    setStartDate(moment(value, 'DD-MM-YYYY', true).isValid() ? value.toDate() : '');
  };
  const handleEndDateChange = (value) => {
    setEndDate(moment(value, 'DD-MM-YYYY', true).isValid() ? value.toDate() : '');
  };
  const validEndDate = current => current.isBefore(DateTime.moment()) && current.isAfter(startDate);
  const handleInstrumentListChange = (selected) => {
    setSelectedInstrumentList(selected);
  };
  const handleTypeTagChange = (selected) => {
    setSelectedTypeTag(selected);
  };

  return (
    <form id="adv-search-form" className="p-3 bg-light">
      <h5 className="mb-3">Advanced Search</h5>
      <div className="row mb-3">
        <div className="col-12">
          <label htmlFor="select-start-date">Filter by Date created</label>
          <div className="row">
            <div className="col-sm-6">
              <DateTime
                id="select-start-date"
                inputProps={{ placeholder: 'Select start date' }}
                timeFormat={false}
                dateFormat="DD-MM-YYYY"
                isValidDate={validStartDate}
                closeOnSelect
                value={startDate}
                onChange={handleStartDateChange}
              />
            </div>
            <div className="col-sm-6">
              <DateTime
                inputProps={{ placeholder: 'Select end date' }}
                timeFormat={false}
                dateFormat="DD-MM-YYYY"
                isValidDate={validEndDate}
                closeOnSelect
                value={endDate}
                onChange={handleEndDateChange}
              />
            </div>
          </div>
        </div>
      </div>
      <div className="row mb-3">
        <div className="col-12">
          <label htmlFor="modelType">Search In</label>
          <Typeahead
            id="modelType"
            multiple
            onChange={(selected) => { handleTypeTagChange(selected); }}
            options={typeOptions}
            placeholder="Search in Experiments, Datasets or Datafiles"
            defaultSelected={typeOptions.slice(0, 3)}
          />
        </div>
      </div>
      <div className="row mb-3 d-{instrumentList.length > 0 ? {'block'} : {'none'}}">
        <div className="col-12">
          <label htmlFor="instrumentList">Filter by Instrument</label>
          <Typeahead
            id="instrumentList"
            multiple
            labelKey="name"
            onChange={(selected) => { handleInstrumentListChange(selected); }}
            placeholder="Start typing to select instruments"
            options={instrumentList}
          />
        </div>
      </div>
      {isLoading && (
        <div className="clearfix float-end mt-1">
          <div className="spinner-border spinner-border-sm text-primary" role="status">
            <span className="sr-only">Loading...</span>
          </div>
        </div>
      )}
      <button
        type="submit"
        className="btn btn-primary"
        onClick={handleAdvancedSearchFormSubmit}
      >
        <i className="fa fa-search" />
        &nbsp;
        Search
      </button>
    </form>
  );
}
AdvancedSearchForm.propTypes = {
  showResults: PropTypes.func.isRequired,
  searchText: PropTypes.string.isRequired,
};

export default AdvancedSearchForm;
