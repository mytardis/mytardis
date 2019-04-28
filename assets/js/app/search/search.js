import React, { useState, } from "react";
import { Component, } from "react";
import {TypeTags, IntrumentTags} from "./tags.js" ;
import SearchDatePicker from "./datepicker";

function Search() {
    const [simpleSearch, setSimpleSerach] = useState("")
    const [advanceSearchVisible, setAdvanceSearchVisible ] = useState(false)
    const toggleAdvanceSearch = () => setAdvanceSearchVisible(!advanceSearchVisible)
    return (
        <main>
            <SimpleSearchForm></SimpleSearchForm>
                <button type="button"
                        onClick={toggleAdvanceSearch}
                        className="btn btn-default dropdown-toggle"
                        data-toggle="dropdown" aria-expanded="false">
                    <span className="caret"></span>
                </button>
            {advanceSearchVisible ? (<AdvanceSearchForm></AdvanceSearchForm>) :
                (<button type="submit" className="simple-search btn btn-primary">
                    <span className="glyphicon glyphicon-search" aria-hidden="true"></span>
                </button>)}
        </main>
    )
}

function SimpleSearchForm() {
    const [simpleSearchText, setSimpleSearchText] = useState("");
    const handleSimpleSearchSubmit = e => {
        e.preventDefault();
        //form validation
        console.log(simpleSearchText)
    }
    const showAdvanceSearchForm = e => {
        e.preventDefault();
    }
    return (
        <form onSubmit={handleSimpleSearchSubmit} id={"simple-search"}>
                <input type="text"
                       name="simple_search_text"
                       onChange={event => setSimpleSearchText(event.target.value)}
                       value={simpleSearchText}
                       className="form-control"
                       placeholder="Search for Experiments, Datasets, Datafiles">
                </input>
        </form>
    )
}

function AdvanceSearchForm() {
    const [advanceSearchText, setAdvanceSeacrhText] = useState("");
    const handleAdvanceSearchSubmit = e => {
        e.preventDefault();
        //form validation
        console.log(advanceSeacrhText)
    }
    const handleAdvanceSearchTextChange = e => {
        e.preventDefault();
        //form validation
        console.log(advanceSeacrhText)
    }
    return (
        <form id="adv-search-form" onSubmit={handleAdvanceSearchSubmit} className="form-horizontal" role="form">
            <div className="form-group" id={"adv-search"}>
                <label htmlFor="filter">Search </label>
                <input type="text" name="adv_search_text" value={advanceSearchText}
                       onChange={handleAdvanceSearchTextChange}
                       className="form-control">
                </input>
                <label htmlFor="filter">Select Date Range</label>
                <SearchDatePicker className="form-control"></SearchDatePicker>
                <label htmlFor="contain">Search In</label>
                <TypeTags className="form-control"></TypeTags>
                <label htmlFor="contain">Instrument</label>
                <IntrumentTags className="form-group"></IntrumentTags>
                <button type="submit" className="btn btn-primary">
                    <span className="glyphicon glyphicon-search" aria-hidden="true"></span>
                </button>
            </div>
        </form>
    )

}

export default Search;