import React, {useState,} from "react";
import {IntrumentTags, TypeTags} from "./tags.js";
import SearchDatePicker from "./datepicker";


function createExperimentResultData(hits, newResults) {
    hits.forEach(function(hit) {
        let created_time = new Date(hit._source.created_time).toString();
        let update_time = new Date(hit._source.update_time).toString();
        newResults = [...newResults, {
            title: hit._source.title,
            type: "experiment",
            id: hit._source.id,
            url: "/experiment/view/" + hit._source.id,
            description : hit._source.description,
            institution_name: hit._source.institution_name,
            created_time: created_time,
            update_time: update_time,
            created_by: hit._source.created_by.first_name + " " + hit._source.created_by.last_name
        }
        ];
    });
    return newResults;
}
function createDatasetResultData(hits, newResults) {
    hits.forEach(function(hit) {
        let created_time = new Date(hit._source.created_time).toString();
        let update_time = new Date(hit._source.modified_time).toString();
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
        let created_time = new Date(hit._source.created_time).toString();
        let update_time = new Date(hit._source.modification_time).toString();
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
        let newResults = []
        let counts = {"experimentsCount": "",
            "datasetsCount":"",
            "datafilesCount":""
        }
        const experimentsHits = result.objects[0].hits["experiments"];
        //create experiment result
        newResults = createExperimentResultData(experimentsHits, newResults);
        counts.experimentsCount = experimentsHits.length;
        // create dataset result
        const datasetHits = result.objects[0].hits["datasets"];
        newResults = createDatasetResultData(datasetHits, newResults);
        counts.datasetsCount = datasetHits.length;
        //create datafile results
        const datafileHits = result.objects[0].hits["datafiles"];
        newResults = createDataFileResultData(datafileHits, newResults);
        counts.datafilesCount = datafileHits.length;
        setResults(newResults);
        setCounts(counts);
    };
    return (
        <main>
            <SimpleSearchForm showResults={showResults}/>
            {results.length > 0 ? <Results results={results} counts={counts}/> : <span/>}
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
                        <div><span style={{fontWeight: "bold"}}>Instrument: </span> {result.instrument}</div>
                        <div><span style={{fontWeight: "bold"}}>Date Created: </span> {result.created_time}</div>
                        <div><span style={{fontWeight: "bold"}}>Last updated: </span> {result.update_time}</div>
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
                        <div><span style={{fontWeight: "bold"}}>Created by: </span> {result.created_by}</div>
                        <div><span style={{fontWeight: "bold"}}>Description: </span> {result.description}</div>
                        <div><span style={{fontWeight: "bold"}}>Institution Name: </span> {result.institution_name}</div>
                        <div><span style={{fontWeight: "bold"}}> Date created: </span> {result.created_time}</div>
                        <div><span style={{fontWeight: "bold"}}> Last updated: </span> {result.update_time}</div>
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
                        <div><span style={{fontWeight: "bold"}}>File Name: </span> {result.title}</div>
                        <div><span style={{fontWeight: "bold"}}> Date created: </span> {result.created_time}</div>
                        <div><span style={{fontWeight: "bold"}}> Last updated: </span> {result.update_time}</div>
                        <span style={{
                            fontSize: 11,
                            fontStyle: "italic"
                        }}>This datafile is from following dataset: </span>
                        <div><span style={{fontWeight: "bold", marginLeft: 5}}><a href={result.dataset_url}>{result.dataset_description}</a></span> </div>
                    </div>
                </div>
            </div>
        )
    };
    return (
        <div className="result" id={result.type}>
            <div className="panel panel-default">
                <div className="panel-body">
                    {result.type == "dataset" &&
                    <div>
                            <button type="button"
                                    onClick={dataToggler}
                                    className="btn btn-link"
                                    data-target="#data"
                                    name={"showChild"}>
                                <i className={dataToggleClass ? "fa fa-plus" : "fa fa-minus"}/>
                            </button>
                                <a style={{fontWeight: "bold"}} href={result.url}>{result.title}</a>
                                <div id={"data"}>{!dataToggleClass && getDatasetData(result)}
                                </div>
                    </div>
                    }
                    {result.type == "experiment" &&
                    <div>
                        <button type="button"
                            onClick={dataToggler}
                            className="btn btn-link"
                            data-target="#data"
                            name={"showChild"}>
                            <i className={dataToggleClass ? "fa fa-plus" : "fa fa-minus"}/>
                        </button>
                        <a style={{fontWeight: "bold"}} href={result.url}>{result.title}</a>
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
            < div id = "exTab1" className = "container" >
                < ul className = "nav nav-pills" style={{padding: 10}} >
                    < li className = "active" >
                        <a href = "#1a" data-toggle = "tab" style={{display: "inline"}}> Experiments </a>
                        <span className="badge badge-light">{counts.experimentsCount}</span>
                    </li>
                    <li>
                        <a href="#2a" data-toggle="tab" style={{display: "inline"}}>Datasets</a>
                        <span className="badge badge-light">{counts.datasetsCount}</span>
                    </li>
                    <li>
                        <a href="#3a" data-toggle="tab" style={{display: "inline"}}>Datafiles</a>
                        <span className="badge badge-light">{counts.datafilesCount}</span>
                    </li>
                </ul>
                <div className="tab-content clearfix">
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
function SimpleSearchForm({showResults}) {
    const [simpleSearchText, setSimpleSearchText] = useState("");
    const [advanceSearchVisible, setAdvanceSearchVisible ] = useState(false);
    const toggleAdvanceSearch = () => setAdvanceSearchVisible(!advanceSearchVisible);
    const handleSimpleSearchSubmit = e => {
        e.preventDefault();
        //fetch results
        fetch('/api/v1/search-v2_simple-search/?query='+simpleSearchText)
            .then(response => response.json())
            .then(data => showResults(data));
        //display results
        console.log(simpleSearchText)
    }
    return (
        <main>
            <form onSubmit={handleSimpleSearchSubmit} id={"simple-search"}>
                <input type="text"
                       name="simple_search_text"
                       onChange={event => setSimpleSearchText(event.target.value)}
                       value={simpleSearchText}
                       className="form-control"
                       placeholder="Search for Experiments, Datasets, Datafiles">
                </input>
            </form>
            <button type="button"
                    onClick={toggleAdvanceSearch}
                    className="btn btn-default dropdown-toggle"
                    data-toggle="dropdown" aria-expanded="false">
                <span className="caret"/>
            </button>
            {advanceSearchVisible ? (<AdvanceSearchForm/>) :
                (<button type="submit" className="simple-search btn btn-primary" onClick={handleSimpleSearchSubmit}>
                    <span className="glyphicon glyphicon-search" aria-hidden="true"/>
                </button>)}

        </main>
    )
}

function AdvanceSearchForm() {
    const [advanceSearchText, setAdvanceSeacrhText] = useState("");
    const handleAdvanceSearchSubmit = e => {
        e.preventDefault();
        //form validation
        console.log(advanceSearchText)
    };
    const handleAdvanceSearchTextChange = e => {
        e.preventDefault();
        //form validation
        console.log(advanceSearchText)
    };
    return (
        <form id="adv-search-form" onSubmit={handleAdvanceSearchSubmit} className="form-horizontal" role="form">
            <div className="form-group" id={"adv-search"}>
                <label htmlFor="filter">Search </label>
                <input type="text" name="adv_search_text" value={advanceSearchText}
                       onChange={e => setAdvanceSeacrhText(e.target.value)}
                       className="form-control">
                </input>
                <label htmlFor="filter">Select Date Range</label>
                <SearchDatePicker className="form-control"/>
                <label htmlFor="contain">Search In</label>
                <TypeTags className="form-control"/>
                <label htmlFor="contain">Instrument</label>
                <IntrumentTags className="form-group"/>
                <button type="submit" className="btn btn-primary">
                    <span className="glyphicon glyphicon-search" aria-hidden="true"/>
                </button>
            </div>
        </form>
    )
}

export default Search;
