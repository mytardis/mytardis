import React, {Component} from "react";

const ReactTags = require("react-tag-autocomplete");


class TypeTags extends Component {
    constructor(props) {
        super(props);

        this.state = {
            tags: [

            ],
            suggestions: [
                {id: 1, name: "Experiments"},
                {id: 2, name: "Dataset"},
                {id: 3, name: "Datafiles"},
            ]
        };
    }

    handleDelete(i) {
        const tags = this.state.tags.slice(0);
        tags.splice(i, 1);
        this.setState({tags});
    }

    handleAddition(tag) {
        const tags = [].concat(this.state.tags, tag);
        this.setState({tags});
    }

    render() {
        return (
            <ReactTags
                autoresize={false}
                placeholder={'Start typing to search in Experiments, Datasets and DataFiles'}
                tags={this.state.tags}
                suggestions={this.state.suggestions}
                handleDelete={this.handleDelete.bind(this)}
                handleAddition={this.handleAddition.bind(this)}/>
        );
    }
}

class IntrumentTags extends Component {
    constructor(props) {
        super(props);

        this.state = {
            tags: [

            ],
            suggestions: [
                {id: 1, name: "Instrument 1"},
                {id: 2, name: "Instrument 2"},
                {id: 3, name: "Instrument 3"},
                {id: 4, name: "Instrument 4"},
                {id: 5, name: "Instrument 5"},
                {id: 6, name: "Instrument 6"},
            ]
        };
    }

    handleDelete(i) {
        const tags = this.state.tags.slice(0);
        tags.splice(i, 1);
        this.setState({tags});
    }

    handleAddition(tag) {
        const tags = [].concat(this.state.tags, tag);
        this.setState({tags});
    }

    render() {
        return (
            <ReactTags
                autoresize={false}
                placeholder={'Start typing to filter by Instrument'}
                tags={this.state.tags}
                suggestions={this.state.suggestions}
                handleDelete={this.handleDelete.bind(this)}
                handleAddition={this.handleAddition.bind(this)}/>
        );
    }
}
export {TypeTags, IntrumentTags}