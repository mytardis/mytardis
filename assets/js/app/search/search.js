import React, {useState, useEffect} from "react";
import DateTime from 'react-datetime';
import { Typeahead} from 'react-bootstrap-typeahead';
import 'react-bootstrap-typeahead/css/Typeahead.css';
import 'react-datetime/css/react-datetime.css';

const queryString = require('query-string');
const parsed = queryString.parse(location.search);
const moment = require('moment');
const csrftoken = getCookie('csrftoken');

function createExperimentResultData(hits, newResults) {
    hits.forEach(function(hit) {
        let created_time = new Date(hit._source.created_time).toDateString();
        let update_time = new Date(hit._source.update_time).toDateString();
        let description = hit._source.description;
        if (description === ""){
            description = "No description available for this experiment"
        }
        newResults = [...newResults, {
            title: hit._source.title,
            type: "experiment",
            id: hit._source.id,
            url: "/experiment/view/" + hit._source.id,
            description : description,
            institution_name: hit._source.institution_name,
            created_time: created_time,
            update_time: update_time,
            created_by: hit._source.created_by.username
        }
        ];
    });
    return newResults;
}
function createDatasetResultData(hits, newResults) {
    hits.forEach(function(hit) {
        let created_time = new Date(hit._source.created_time).toDateString();
        let update_time = new Date(hit._source.modified_time).toDateString();
        newResults = [...newResults, {
            title: hit._source.description,
            type: "dataset",
            id: hit._source.id,
            url: "/dataset/" + hit._source.id,
            experiments: hit._source.experiments,
            instrument: hit._source.instrument.name,
            created_time: created_time,
            update_time: update_time
        }
        ];
    });
    return newResults;
}
function createDataFileResultData(hits, newResults) {
    hits.forEach(function(hit) {
        let created_time = new Date(hit._source.created_time).toDateString();
        let update_time = new Date(hit._source.modification_time).toDateString();
        newResults = [...newResults, {
            title: hit._source.filename,
            type: "datafile",
            id: hit._source.id,
            url: "/datafile/view/" + hit._id,
            created_time: created_time,
            update_time: update_time,
            dataset_description: hit._source.dataset.description,
            dataset_url: "/dataset/" + hit._source.dataset.id
        }
        ];
    });
    return newResults;
}

function Search() {
    const [results, setResults] = useState([]);
    const [counts, setCounts] = useState([]);

    const showResults = result => {
        let newResults = [];
        let counts = {"experimentsCount": 0,
            "datasetsCount":0,
            "datafilesCount":0
        };
        const experimentsHits = result.hits["experiments"];
        //create experiment result
        newResults = createExperimentResultData(experimentsHits, newResults);
        counts.experimentsCount = experimentsHits.length;
        // create dataset result
        const datasetHits = result.hits["datasets"];
        newResults = createDatasetResultData(datasetHits, newResults);
        counts.datasetsCount = datasetHits.length;
        //create datafile results
        const datafileHits = result.hits["datafiles"];
        newResults = createDataFileResultData(datafileHits, newResults);
        counts.datafilesCount = datafileHits.length;
        setResults(newResults);
        setCounts(counts);
    };
    return (
        <main>
            <SimpleSearchForm showResults={showResults} searchText={parsed.q}/>
            {<Results results={results} counts={counts}/>}
        </main>
    );
}
function Result({result}) {
    const [dataToggleClass, setDataToggleClass] = useState(false);
    const dataToggler = () => {
        setDataToggleClass(!dataToggleClass)
    };
    const getDatasetData = (result) => {
        return (
            <div className={"accordion-group"} style={{marginLeft: 20}}>
                <div className={"accordion-heading"}>
                    <div className={"accordion-body"}>
                        <span style={{
                            fontSize: 11,
                            fontStyle: "italic"
                        }}>This dataset belongs to following {result.experiments.length} experiment: </span>
                        <ul>
                            {result.experiments.map(function(res, index) {
                                return <li key={index}><a href={"/experiment/view/" + res.id}>{res.title}</a></li>;
                            })}
                        </ul>
                    </div>
                </div>
            </div>
        )
    };
    const getExperimentData = (result) => {
        return(
            <div className={"accordion-group"} style={{marginLeft: 20 }}>
                <div className={"accordion-heading"}>
                    <div className={"accordion-body"}>
                        <div>{result.description}</div>
                    </div>
                </div>
            </div>
        )
    };
    const getDataFileData = (result) => {
        return(
            <div className={"accordion-group"} style={{marginLeft: 20 }}>
                <div className={"accordion-heading"}>
                    <div className={"accordion-body"}>
                        <span style={{
                            fontSize: 11,
                            fontStyle: "italic"
                        }}>This datafile is from following dataset: </span>
                        <div><span style={{fontWeight: "bold", marginLeft: 5}}>
                            <a href={result.dataset_url}>{result.dataset_description}</a></span>
                        </div>
                    </div>
                </div>
            </div>
        )
    };
    return (
        <div className="result" id={result.type}>
            <div className="panel panel-default">
                <div className="panel-body">
                    {result.type === "dataset" &&
                    <div>
                        <button type="button"
                                onClick={dataToggler}
                                className="btn btn-link"
                                data-target="#data"
                                name={"showChild"}>
                                <i className={dataToggleClass ? "fa fa-plus" : "fa fa-minus"}/>
                        </button>
                        <a style={{fontWeight: "bold"}} href={result.url}>{result.title}</a>
                        <ul className="nav nav-pills badgelist pull-right"
                            style={{display:"inline-block"}}>
                            <li className="pull-right">
                                <span className="label label-info" title={"Date Created: "+result.created_time} >
                                    <i className="fa fa-clock-o"/>
                                    <span>
                                        {result.created_time}
                                    </span>
                                </span>
                            </li>
                            <li className="pull-right">
                                <span className="label label-info" title={"Institution Name: "+result.institution_name} >
                                    {/*upgrade to font-awesome 5 will bring this icon */}
                                    <i className="fa fa-microscope"/>
                                    <span>
                                        {result.instrument}
                                    </span>
                                </span>
                            </li>
                        </ul>
                        <div id={"data"}>{!dataToggleClass && getDatasetData(result)}
                        </div>
                    </div>
                    }
                    {result.type === "experiment" &&
                    <div>
                        <button type="button"
                            onClick={dataToggler}
                            className="btn btn-link"
                            data-target="#data"
                            name={"showChild"}>
                            <i className={dataToggleClass ? "fa fa-plus" : "fa fa-minus"}/>
                        </button>
                        <a style={{fontWeight: "bold", display:"inline-block"}} href={result.url}>{result.title}</a>
                        <ul className="nav nav-pills badgelist pull-right" style={{display:"inline-block"}}>
                            <li className="pull-right">
                                <span className="label label-info" title={"Date Created: "+result.created_time} >
                                    <i className="fa fa-clock-o"/>
                                    <span>
                                        {result.created_time}
                                    </span>
                                </span>
                            </li>
                            <li className="pull-right">
                                <span className="label label-info" title={"Created by: "+result.created_by} >
                                    <i className="fa fa-user"/>
                                    <span>
                                        {result.created_by}
                                    </span>
                                </span>
                            </li>
                            <li className="pull-right">
                                <span className="label label-info" title={"Institution Name: "+result.institution_name} >
                                    <i className="fa fa-institution"/>
                                    <span>
                                        {result.institution_name}
                                    </span>
                                </span>
                            </li>
                        </ul>
                        <div id={"data"}>{! dataToggleClass && getExperimentData(result)}</div>
                    </div>
                    }
                    {result.type == "datafile" &&
                    <div>
                        <button type="button"
                            onClick={dataToggler}
                            className="btn btn-link"
                            data-target="#data"
                            name={"showChild"}>
                            <i className={dataToggleClass ? "fa fa-plus" : "fa fa-minus"}/>
                        </button>
                        <a style={{fontWeight: "bold"}} href={result.url}>{result.title}</a>
                        <ul className="nav nav-pills badgelist pull-right" style={{display:"inline-block"}}>
                            <li className="pull-right">
                                <span className="label label-info" title={"Date Created: "+result.created_time} >
                                    <i className="fa fa-clock-o"/>
                                    <span>
                                        {result.created_time}
                                    </span>
                                </span>
                            </li>
                        </ul>
                        <div id={"data"}>{! dataToggleClass && getDataFileData(result)}</div>
                    </div>
                    }
                </div>
            </div>
        </div>
    );
}

function Results({results, counts}) {
    return (
        <div style={{marginTop: 15}}>
            <div className="container" style={{marginBottom: 10}}>
                <h2>Search Results </h2>
            </div>
            < div id = "tabbed-pane" className = "container" >
                < ul className = "nav nav-tabs" style={{"fontWeight": 600}}>
                    < li className = "active" >

                        <a href = "#1a" data-toggle = "tab" >
                            <i className="fa fa-flask fa-2x"/>Experiments
                            <span className="badge badge-light">{counts.experimentsCount}</span>
                             </a>
                    </li>
                    <li>

                        <a href="#2a" data-toggle="tab">
                            <i className="fa fa-folder fa-2x"/>Datasets
                        <span className="badge badge-light">{counts.datasetsCount}</span>
                            </a>
                    </li>
                    <li>

                        <a href="#3a" data-toggle="tab" >
                            <i className="fa fa-file fa-2x"/>Datafiles
                        <span className="badge badge-light">{counts.datafilesCount}</span>
                            </a>
                    </li>
                </ul>
                <div className="tab-content">
                    <div className="tab-pane active" id="1a">
                        <div className="result-list">
                            {results.map(function(result, index) {
                                let res = "";
                                {result.type == "experiment" ? (
                                    res = <Result
                                    key={index}
                                    result={result}
                                />)
                                : <span/>}
                                return res
                                }
                            )}
                        </div>
                    </div>
                    <div className="tab-pane" id="2a">
                        <div className="result-list">
                           {results.map(function(result, index) {
                                let res = ""
                                {result.type == "dataset" ? (
                                    res = <Result
                                    key={index}
                                    result={result}
                                />)
                                : <span/>}
                                return res
                                }
                            )}
                        </div>
                    </div>
                    <div className="tab-pane" id="3a">
                        <div className="result-list">
                            {results.map(function(result, index) {
                                let res = "";
                                {result.type == "datafile" ? (
                                    res = <Result
                                    key={index}
                                    result={result}
                                />)
                                : <span/>}
                                return res
                                }
                            )}
                        </div>
                    </div>
                </div>
            </div>
        </div>
    )
}
function SimpleSearchForm({showResults, searchText}) {
    const [simpleSearchText, setSimpleSearchText] = useState(searchText);
    const [advanceSearchVisible, setAdvanceSearchVisible ] = useState(false);
    const [isLoading, setIsLoading] = useState(false);
    const toggleAdvanceSearch = () => setAdvanceSearchVisible(!advanceSearchVisible);
    const fetchResults = () => {
        //fetch results
        setIsLoading(true);
        fetch('/api/v1/search-v2_simple-search/?query='+simpleSearchText, {
            method: 'get',
            headers: {
                'Accept': 'application/json',
                'Content-Type': 'application/json',
                'X-CSRFToken': csrftoken
            },})
            .then(response => response.json())
            .then(function (data){
                showResults(data.objects[0]);
                setIsLoading(false)
            } );
    };
    const handleSimpleSearchSubmit = e => {
        e.preventDefault();
        fetchResults()
    };
    const handleSimpleSearchTextChange = (e,searchText) => {
         e.preventDefault();
         setSimpleSearchText(searchText);
         handleSimpleSearchSubmit(e)
     };
    useEffect(() => {
       fetchResults()
    }, searchText);
    return (
        <main>
            <form onSubmit={handleSimpleSearchSubmit} id={"simple-search"}>
                <input type="text"
                       name="simple_search_text"
                       onChange={event => handleSimpleSearchTextChange(event, event.target.value)}
                       value={simpleSearchText}
                       className="form-control"
                       placeholder="Search for Experiments, Datasets, Datafiles">
                </input>
            </form>
            {isLoading &&
                <div className="col-md-12" style={{textAlign: "center",  position:"absolute"}}>
                    <div id="spinner" style={{textAlign: "center"}}>
                        <i id="mo-spin-icon" className="fa fa-spinner fa-pulse fa-2x"/>
                    </div>
                </div>
            }
            <button type="button"
                    onClick={toggleAdvanceSearch}
                    className="btn btn-default dropdown-toggle"
                    data-toggle="dropdown" aria-expanded="false">
                <span className="caret"/>
            </button>
            {advanceSearchVisible ? (<AdvanceSearchForm searchText={simpleSearchText} showResults={showResults}/>) :
                (<button type="submit" className="simple-search btn btn-primary" onClick={handleSimpleSearchSubmit}>
                    <span className="glyphicon glyphicon-search" aria-hidden="true"/>
                </button>)}

        </main>
    )
}

function AdvanceSearchForm({searchText, showResults}) {
    const [instrumentList, setInstrumentList] = useState([]);
    const typeOptions=["Dataset","Experiment", "Datafile"];
    const [startDate, setStartDate] = useState('');
    const [endDate, setEndDate] = useState('');
    const [isLoading, setIsLoading] = useState(false);
    const [formData, setFormData] = useState({["text"]: searchText,
        ["TypeTag"]: typeOptions});
    const getInstrumentList = () => {
        let tempList = [];
        fetch(`/api/v1/instrument/`)
            .then(resp =>  resp.json())
            .then(json => {
                json.objects.forEach(function (value) {
                    tempList.push(value.name)});
                });
            setInstrumentList(tempList)
    };
    let handleAdvanceSearchFormSubmit = (event) => {
        event.preventDefault();
        setIsLoading(true);
        //set form data
        setFormData(formData => ({...formData, ["text"]: searchText}));
        fetch('/api/v1/search-v2_advance-search/', {
            method: 'post',
            headers: {
                'Accept': 'application/json',
                'Content-Type': 'application/json',
                'X-CSRFToken': csrftoken
            },
            body: JSON.stringify(formData)
            }).then(function(response) {
                return response.json();
                }).then(function(data) {
                    setIsLoading(false);
                    showResults(data)
                });
    };
    let validStartDate = function( current ){
        return current.isBefore( DateTime.moment() );
        };
    let handleStartDateChange = (value) => {
        setFormData(formData => ({...formData, ["StartDate"]: value.toDate()}));
        setStartDate(value.toDate());
    };
    let handleEndDateChange = (value) => {
        setFormData(formData => ({...formData, ["EndDate"]: value.toDate()}));
    };
    let validEndDate = function(current){
        return current.isBefore( DateTime.moment() ) && current.isAfter(startDate)
    };
    let handleInstrumentListChange = (selected) => {
        setFormData(formData => ({...formData, ["InstrumentList"]: selected}));
    };
    let handleTypeTagChange = (selected) => {
        setFormData(formData => ({...formData, ["TypeTag"]: selected}));
    };

    return (

        <form id="adv-search-form" className="form-horizontal" role="form">
            <div className="form-group" id={"adv-search"}>
                <label htmlFor="filter">Filter by Date created</label>
                <div className="form-group row">
                    <div className="col-xs-6" style={{paddingLeft:0, paddingRight:15}}>
                        <DateTime inputProps={{placeholder: "Select start date"}}
                                  timeFormat={false}
                                  dateFormat="DD-MM-YYYY"
                                  isValidDate={ validStartDate }
                                  closeOnSelect={true}
                                  onChange = {handleStartDateChange}
                        />
                    </div>
                    <div className="col-xs-6" style={{paddingRight:0}}>
                        <DateTime inputProps={{placeholder: "Select end date"}}
                                  timeFormat={false}
                                  dateFormat="DD-MM-YYYY"
                                  isValidDate = { validEndDate }
                                  closeOnSelect={true}
                                  value={endDate}
                                  onChange = {handleEndDateChange}
                        />
                    </div>
                </div>

                <label htmlFor="contain">Search In</label>
                <Typeahead
                    multiple
                    onChange={(selected) => {handleTypeTagChange(selected)}}
                    options={typeOptions}
                    placeholder="Search in Experiments, Datasets or Datafiles"
                    defaultSelected={typeOptions.slice(0, 3)}
                />
                <label htmlFor="contain">Filter by Instrument</label>
                <Typeahead
                    multiple
                    onFocus={() => getInstrumentList()}
                    onChange={(selected) => {handleInstrumentListChange(selected)}}
                    placeholder="Start typing to select instruments"
                    options={instrumentList}
                />
                <button type="submit"
                        className="btn btn-primary"
                        onClick={handleAdvanceSearchFormSubmit}
                >
                    <span className="glyphicon glyphicon-search" aria-hidden="true"/>
                </button>
                {isLoading &&
                <div className="col-md-6" style={{textAlign: "center",  position:"absolute"}}>
                    <div id="spinner" style={{textAlign: "center"}}>
                        <i id="mo-spin-icon" className="fa fa-spinner fa-pulse fa-2x"/>
                    </div>
                </div>
                }
            </div>
        </form>

    )
}
export default Search;
