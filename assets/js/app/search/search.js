import React, {Component} from "react";
import {TypeTags, IntrumentTags} from "./tags.js" ;
import SearchDatePicker from "./datepicker";

class Search extends Component {
    render() {
        return (
            <div className="container">
                <div className="row">
                    <div className="col-md-10">
                        <div className="input-group" id={"adv-search"}>
                            <input type="text" className="form-control"
                                   placeholder="Search for Experiments, Datasets, Datafiles"/>
                            <div className="input-group-btn">
                                <div className="btn-group" role="group">
                                    <div className="dropdown dropdown-lg">
                                        <button type="button" className="btn btn-default dropdown-toggle"
                                                data-toggle="dropdown" aria-expanded="false"><span
                                            className="caret"></span></button>
                                        <div className="dropdown-menu dropdown-menu-right" role="menu">
                                            <form className="form-horizontal" role="form">
                                                <div className="form-group">
                                                    <label htmlFor="filter">Search </label>
                                                    <input type="text" className="form-control"></input>
                                                </div>
                                                <div className="form-group">
                                                    <label htmlFor="filter">Select Date Range</label>
                                                     <SearchDatePicker className="form-control"></SearchDatePicker>
                                                </div>
                                                <div className="form-group">
                                                    <label htmlFor="contain">Search In</label>
                                                    <TypeTags className="form-control"></TypeTags>
                                                </div>
                                                <div className="form-group">
                                                    <label htmlFor="contain">Instrument</label>
                                                    <IntrumentTags className="form-group"></IntrumentTags>
                                                </div>
                                                <button type="submit" className="btn btn-primary"><span
                                                    className="glyphicon glyphicon-search" aria-hidden="true"></span>
                                                </button>
                                            </form>
                                        </div>
                                    </div>
                                    <button type="button" className="btn btn-primary"><span
                                        className="glyphicon glyphicon-search" aria-hidden="true"></span></button>
                                </div>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        );

    }
}

export default Search;